from flask import Flask, request, jsonify

app = Flask(__name__)

# Endpoint to handle touch sensor POST request
@app.route('/api/touch', methods=['POST'])
def handle_touch():
    try:
        # Get JSON data from the POST request
        data = request.get_json()
        
        if 'message' in data:
            print(f"Received: {data['message']}")
            
            # Respond with a success message
            return jsonify({"status": "success", "message": "Touch event received!"}), 200
        else:
            return jsonify({"status": "error", "message": "Invalid data"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Start the Flask server
    app.run(host='0.0.0.0', port=5000)