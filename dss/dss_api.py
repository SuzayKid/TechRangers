from flask import Flask, request, jsonify
from dss.dss_engine import DSSEngine
from dss.mcp_protocol import MCPProtocol
import os

app = Flask(__name__)
dss_engine = DSSEngine() # Keep for potential fallback or other uses
# Initialize MCPProtocol with LLM and Embedding API URLs from environment variables
LLM_API_URL = os.getenv("LLM_API_URL", "http://localhost:8000/v1/chat/completions")
EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL", "http://localhost:8001/v1/embeddings")
mcp_protocol = MCPProtocol(LLM_API_URL, EMBEDDING_API_URL)

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

    user_query = data.get("query", "")
    input_type = data.get("type")
    input_id = data.get("id")

    village_id = None
    patta_holder_id = None

    if input_type == "village":
        village_id = input_id
    elif input_type == "patta_holder":
        patta_holder_id = input_id
    
    # If no specific location is provided, proceed with just the query
    if not user_query and not (village_id or patta_holder_id):
        return jsonify({"error": "Either 'query' or a valid 'type' and 'id' must be provided."}), 400

    try:
        llm_recommendations = mcp_protocol.get_scheme_recommendations_for_user(
            user_query=user_query,
            village_id=village_id,
            patta_holder_id=patta_holder_id
        )
        
        return jsonify({"recommendations": llm_recommendations}), 200
    except Exception as e:
        print(f"Error in get_recommendations API: {e}")
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    # For development purposes, set environment variables or use a .env file
    # Example:
    # os.environ["DB_HOST"] = "localhost"
    # os.environ["DB_NAME"] = "sih_dss"
    # os.environ["DB_USER"] = "sih_user"
    # os.environ["DB_PASSWORD"] = "sih_password"
    app.run(debug=True, host='0.0.0.0', port=5000)