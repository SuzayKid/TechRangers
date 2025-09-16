import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
import numpy as np
from cv_models.model import UNET
from cv_models.data_preprocessing import SatelliteImageProcessor # Assuming this is ready

# Placeholder for a custom dataset. In a real scenario, this would load processed tiles.
class SatelliteDataset(Dataset):
    def __init__(self, images, masks, transform=None):
        self.images = images
        self.masks = masks
        self.transform = transform

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        image = self.images[idx]
        mask = self.masks[idx]

        # Convert to PyTorch tensor format (C, H, W)
        image = torch.from_numpy(image).permute(2, 0, 1).float()
        # For multi-class, mask should be LongTensor and not have a channel dim if using CrossEntropyLoss
        # If using a different loss (e.g., DiceLoss for multi-class), it might need to be one-hot encoded
        mask = torch.from_numpy(mask).long()

        if self.transform:
            image = self.transform(image)
            # Mask transformations should be applied carefully to maintain alignment
            # For simple transforms like normalization, it's fine.
            # For geometric transforms, they should be applied during preprocessing.

        return image, mask

def train_fn(loader, model, optimizer, loss_fn, scaler, device):
    loop = 0
    for batch_idx, (data, targets) in enumerate(loader):
        data = data.to(device=device)
        targets = targets.to(device=device)

        # forward
        with torch.cuda.amp.autocast():
            predictions = model(data)
            loss = loss_fn(predictions, targets)

        # backward
        optimizer.zero_grad()
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()

        loop += 1
        if loop % 10 == 0:
            print(f"Loss after {loop} batches: {loss.item():.4f}")

def get_metrics(loader, model, device, num_classes):
    # For multi-class, accuracy and Dice score need to be calculated per class or averaged.
    # This is a simplified version for overall accuracy.
    total_correct_pixels = 0
    total_pixels = 0
    model.eval()

    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            y = y.to(device) # y is now (N, H, W) with class indices

            predictions = model(x) # (N, num_classes, H, W)
            predicted_masks = torch.argmax(predictions, dim=1) # (N, H, W) with class indices

            total_correct_pixels += (predicted_masks == y).sum().item()
            total_pixels += torch.numel(y)

    accuracy = total_correct_pixels / total_pixels
    print(f"Overall Accuracy: {accuracy*100:.2f}%")
    # For a more robust evaluation, per-class IoU or F1-score would be calculated.
    model.train()
    return accuracy

def main():
    # Hyperparameters
    LEARNING_RATE = 1e-4
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    BATCH_SIZE = 16
    NUM_EPOCHS = 10
    NUM_WORKERS = 2 # Adjust based on your system
    IMAGE_HEIGHT = 256
    IMAGE_WIDTH = 256
    PIN_MEMORY = True
    LOAD_MODEL = False # Set to True to resume training from a checkpoint

    # Model, Loss, Optimizer
    NUM_CLASSES = 5 # e.g., 4 asset classes + 1 background
    model = UNET(in_channels=3, num_classes=NUM_CLASSES).to(DEVICE)
    loss_fn = nn.CrossEntropyLoss() # For multi-class segmentation
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scaler = torch.cuda.amp.GradScaler() # For mixed precision training

    # Data loading
    # Replace with your actual paths to satellite imagery and label files
    image_path = "path/to/your/training_satellite_image.tif"
    label_path = "path/to/your/training_labels.geojson" # or .shp

    print(f"Loading and preprocessing data from {image_path} and {label_path}...")
    processor = SatelliteImageProcessor(image_path, label_path, tile_size=(IMAGE_HEIGHT, IMAGE_WIDTH))
    processed_images, processed_masks = processor.run_pipeline()
    print(f"Finished preprocessing. Got {len(processed_images)} image tiles and {len(processed_masks)} mask tiles.")
    print(f"Shape of first processed image: {processed_images[0].shape}, mask: {processed_masks[0].shape}")

    # Split data into training and validation sets
    split_idx = int(len(processed_images) * 0.8)
    train_images, val_images = processed_images[:split_idx], processed_images[split_idx:]
    train_masks, val_masks = processed_masks[:split_idx], processed_masks[split_idx:]

    train_dataset = SatelliteDataset(train_images, train_masks)
    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        num_workers=NUM_WORKERS,
        pin_memory=PIN_MEMORY,
        shuffle=True,
    )

    val_dataset = SatelliteDataset(val_images, val_masks)
    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        num_workers=NUM_WORKERS,
        pin_memory=PIN_MEMORY,
        shuffle=False,
    )

    # Training loop
    for epoch in range(NUM_EPOCHS):
        print(f"Epoch {epoch+1}/{NUM_EPOCHS}")
        train_fn(train_loader, model, optimizer, loss_fn, scaler, DEVICE)
        
        # Evaluate on validation set
        get_metrics(val_loader, model, DEVICE, NUM_CLASSES)

if __name__ == "__main__":
    main()