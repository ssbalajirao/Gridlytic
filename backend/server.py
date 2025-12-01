from flask import Flask, jsonify
from flask_cors import CORS # 1. Import CORS

# 2. Initialize the Flask App
app = Flask(__name__)

# 3. Initialize CORS: Allow requests from all origins (for development only)
# This prevents the browser from blocking your React app's requests
CORS(app) 

# 4. Define the API Endpoint
# Route: /api/test
@app.route('/api/test', methods=['GET'])
def test_api_status():
    """
    Returns a simple JSON message to confirm the backend is running.
    """
    # Create the required JSON response: { "message": "backend working" }
    response = {'message': 'backend working'}
    return jsonify(response)

# 5. Run the application
if __name__ == '__main__':
    # Flask runs on http://127.0.0.1:5000 by default
    # debug=True automatically reloads the server on code changes
    app.run(debug=True)