
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__, static_folder='dist')
CORS(app)

# Sample inventory data
inventory_items = [
    {"id": 1, "name": "Medical Supplies", "quantity": 50, "location": "Module A", "expiry_date": "2025-12-31"},
    {"id": 2, "name": "Food Rations", "quantity": 200, "location": "Storage Bay", "expiry_date": "2025-06-30"},
    {"id": 3, "name": "Water Containers", "quantity": 100, "location": "Module B", "expiry_date": "2026-01-15"},
    {"id": 4, "name": "Oxygen Tanks", "quantity": 25, "location": "Airlock", "expiry_date": "2025-09-22"},
    {"id": 5, "name": "Research Equipment", "quantity": 30, "location": "Lab Module", "expiry_date": "2027-03-10"}
]

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    return jsonify(inventory_items)

@app.route('/api/inventory/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if item:
        return jsonify(item)
    return jsonify({"error": "Item not found"}), 404

@app.route('/api/inventory', methods=['POST'])
def add_item():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid data"}), 400
    
    new_id = max([item["id"] for item in inventory_items]) + 1
    new_item = {
        "id": new_id,
        "name": data.get("name", ""),
        "quantity": data.get("quantity", 0),
        "location": data.get("location", ""),
        "expiry_date": data.get("expiry_date", "")
    }
    
    inventory_items.append(new_item)
    return jsonify(new_item), 201

# Serve React app
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
