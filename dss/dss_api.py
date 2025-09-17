from flask import Flask, request, jsonify
from dss.dss_engine import DSSEngine
import os

app = Flask(__name__)
dss_engine = DSSEngine()

@app.route('/api/dss/recommendations', methods=['POST'])
def get_recommendations():
    """
    API endpoint to get scheme recommendations.
    Input: { "type": "village", "id": 123 } or { "type": "patta_holder", "id": 456 }
    Output: A prioritized list of recommended schemes with justifications.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON input"}), 400

    input_type = data.get("type")
    input_id = data.get("id")

    if not input_type or not input_id:
        return jsonify({"error": "Missing 'type' or 'id' in request body"}), 400
    
    if input_type not in ["village", "patta_holder"]:
        return jsonify({"error": "Invalid 'type'. Must be 'village' or 'patta_holder'"}), 400

    try:
        recommendations_result = dss_engine.get_recommendations(input_type, input_id)
        
        if "error" in recommendations_result:
            return jsonify(recommendations_result), 404 # Or appropriate error code
        
        return jsonify(recommendations_result), 200
    except NotImplementedError as e:
        return jsonify({"error": str(e)}), 501
    except Exception as e:
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    # For development purposes, set environment variables or use a .env file
    # Example:
    # os.environ["DB_HOST"] = "localhost"
    # os.environ["DB_NAME"] = "sih_dss"
    # os.environ["DB_USER"] = "sih_user"
    # os.environ["DB_PASSWORD"] = "sih_password"
    app.run(debug=True, host='0.0.0.0', port=5000)