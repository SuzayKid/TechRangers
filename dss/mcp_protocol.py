import os
import numpy as np
from dss.database import fetch_village_dss_data, fetch_eligibility_rules, find_similar_schemes
# Assuming an LLM client and embedding model are available
# from llm_client import LLMClient
# from embedding_model import EmbeddingModel

class MCPProtocol:
    def __init__(self, llm_api_url: str, embedding_api_url: str):
        self.llm_api_url = llm_api_url
        self.embedding_api_url = embedding_api_url
        # self.llm_client = LLMClient(llm_api_url)
        # self.embedding_model = EmbeddingModel(embedding_api_url)
        print(f"MCPProtocol initialized with LLM API: {llm_api_url} and Embedding API: {embedding_api_url}")

    def _generate_embedding(self, text: str) -> np.ndarray:
        """Generates an embedding for the given text using the embedding model."""
        # Placeholder for actual embedding generation
        # In a real scenario, this would call an embedding service/model
        print(f"Generating embedding for text: '{text[:50]}...'")
        return np.random.rand(1536) # Dummy embedding for now

    def _get_llm_response(self, prompt: str) -> str:
        """Gets a response from the LLM based on the prompt."""
        # Placeholder for actual LLM interaction
        # In a real scenario, this would call the LLM client
        print(f"Getting LLM response for prompt: '{prompt[:100]}...'")
        return "This is a dummy LLM response based on the provided context."

    def get_scheme_recommendations_for_user(self, user_query: str, village_id: int = None, patta_holder_id: int = None):
        """
        Orchestrates fetching data, constructing context, and getting LLM recommendations.
        """
        context_parts = []

        # 1. Fetch user/village specific DSS data
        if village_id:
            village_data = fetch_village_dss_data(village_id=village_id)
            if village_data:
                context_parts.append(f"User is in Village ID {village_id} with the following attributes: {village_data}")
            else:
                context_parts.append(f"No DSS data found for Village ID {village_id}.")
        elif patta_holder_id:
            # TODO: Implement logic to get village_id from patta_holder_id and then fetch data
            context_parts.append(f"Patta holder ID {patta_holder_id} provided. Village data fetching by patta_holder_id is not yet implemented.")
        else:
            context_parts.append("No specific location provided for the user.")

        # 2. Fetch all eligibility rules and scheme descriptions
        all_schemes_and_rules = fetch_eligibility_rules()
        if all_schemes_and_rules:
            context_parts.append("\nAvailable Schemes and their Eligibility Rules:")
            for rule in all_schemes_and_rules:
                context_parts.append(f"- Scheme: {rule['scheme_name']}, Description: {rule['description']}, Rule: {rule['attribute']} {rule['operator']} {rule['value']}")
        else:
            context_parts.append("No schemes or eligibility rules found in the database.")

        # 3. Perform vector similarity search based on user query
        if user_query:
            query_embedding = self._generate_embedding(user_query)
            similar_schemes = find_similar_schemes(query_embedding)
            if similar_schemes:
                context_parts.append("\nSchemes semantically similar to your query:")
                for scheme in similar_schemes:
                    context_parts.append(f"- Scheme: {scheme['scheme_name']}, Description: {scheme['description']}")
            else:
                context_parts.append("No schemes found semantically similar to your query.")

        # 4. Construct the final prompt for the LLM
        full_context = "\n".join(context_parts)
        prompt = f"""
        You are a helpful assistant for the Digital Scheme Selector (DSS).
        Based on the following context, provide recommendations for government schemes applicable to the user.
        Explain why each scheme is applicable or not, considering the user's location data and the scheme's eligibility rules.
        If a user query is provided, also consider schemes semantically similar to the query.

        User Query: "{user_query}"

        Context:
        {full_context}

        Please provide a clear and concise response, suitable for a non-technical person.
        """

        # 5. Get response from LLM
        llm_response = self._get_llm_response(prompt)
        return llm_response

# Example Usage (for testing purposes)
if __name__ == "__main__":
    # These URLs would typically come from environment variables or a config file
    LLM_API_URL = os.getenv("LLM_API_URL", "http://localhost:8000/v1/chat/completions")
    EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL", "http://localhost:8001/v1/embeddings")

    mcp = MCPProtocol(LLM_API_URL, EMBEDDING_API_URL)

    # Example 1: User in a specific village, asking a general question
    print("--- Example 1: Village ID 1, general query ---")
    response1 = mcp.get_scheme_recommendations_for_user(
        user_query="What schemes are available for farmers?",
        village_id=1
    )
    print(response1)

    # Example 2: User without specific location, asking about water conservation
    print("\n--- Example 2: No village ID, water conservation query ---")
    response2 = mcp.get_scheme_recommendations_for_user(
        user_query="I am interested in schemes related to water conservation and irrigation.",
        village_id=None
    )
    print(response2)