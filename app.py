from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import json

app = Flask(__name__, static_folder='dist')
CORS(app)

# Define the data file path
DATA_FILE = os.path.join('data', 'inventory.json')

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

# Load data from file or use sample data
def load_inventory():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return default_inventory()
    else:
        data = default_inventory()
        save_inventory(data)
        return data

# Save data to file
def save_inventory(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# Default inventory if no file exists
def default_inventory():
    return [
        {"id": 1, "name": "Medical Supplies", "quantity": 50, "location": "Module A", "expiry_date": "2025-12-31"},
        {"id": 2, "name": "Food Rations", "quantity": 200, "location": "Storage Bay", "expiry_date": "2025-06-30"},
        {"id": 3, "name": "Water Containers", "quantity": 100, "location": "Module B", "expiry_date": "2026-01-15"},
        {"id": 4, "name": "Oxygen Tanks", "quantity": 25, "location": "Airlock", "expiry_date": "2025-09-22"},
        {"id": 5, "name": "Research Equipment", "quantity": 30, "location": "Lab Module", "expiry_date": "2027-03-10"}
    ]

# Initialize inventory
inventory_items = load_inventory()

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
    
    # Validate required fields
    required_fields = ["name", "quantity", "location"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    new_id = 1
    if inventory_items:
        new_id = max([item["id"] for item in inventory_items]) + 1
        
    new_item = {
        "id": new_id,
        "name": data.get("name", ""),
        "quantity": data.get("quantity", 0),
        "location": data.get("location", ""),
        "expiry_date": data.get("expiry_date", "")
    }
    
    inventory_items.append(new_item)
    save_inventory(inventory_items)
    return jsonify(new_item), 201

@app.route('/api/inventory/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        return jsonify({"error": "Item not found"}), 404
        
    data = request.json
    if not data:
        return jsonify({"error": "Invalid data"}), 400
        
    for key in data:
        if key in item and key != "id":  # Prevent ID changes
            item[key] = data[key]
    
    save_inventory(inventory_items)        
    return jsonify(item)

@app.route('/api/inventory/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    global inventory_items
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        return jsonify({"error": "Item not found"}), 404
        
    inventory_items = [item for item in inventory_items if item["id"] != item_id]
    save_inventory(inventory_items)
    return jsonify({"message": "Item deleted successfully"})

# Serve React app
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=8000, debug=debug_mode)
