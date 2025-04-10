from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import json
import datetime
import uuid

app = Flask(__name__, static_folder='dist')
CORS(app)

# Define the data file paths
DATA_DIR = 'data'
INVENTORY_FILE = os.path.join(DATA_DIR, 'inventory.json')
CONTAINERS_FILE = os.path.join(DATA_DIR, 'containers.json')
LOGS_FILE = os.path.join(DATA_DIR, 'logs.json')
WASTE_FILE = os.path.join(DATA_DIR, 'waste.json')

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize data structures
def load_data(file_path, default_func):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except:
            return default_func()
    else:
        data = default_func()
        save_data(file_path, data)
        return data

def save_data(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

# Default data functions
def default_inventory():
    return [
        {"id": 1, "name": "Medical Supplies", "quantity": 50, "location": "Module A", "expiry_date": "2025-12-31", "container_id": 1},
        {"id": 2, "name": "Food Rations", "quantity": 200, "location": "Storage Bay", "expiry_date": "2025-06-30", "container_id": 2},
        {"id": 3, "name": "Water Containers", "quantity": 100, "location": "Module B", "expiry_date": "2026-01-15", "container_id": 3},
        {"id": 4, "name": "Oxygen Tanks", "quantity": 25, "location": "Airlock", "expiry_date": "2025-09-22", "container_id": 4},
        {"id": 5, "name": "Research Equipment", "quantity": 30, "location": "Lab Module", "expiry_date": "2027-03-10", "container_id": 5}
    ]

def default_containers():
    return [
        {"id": 1, "name": "Medical Cabinet", "capacity": 100, "current_fill": 50, "location": "Module A"},
        {"id": 2, "name": "Food Storage", "capacity": 300, "current_fill": 200, "location": "Storage Bay"},
        {"id": 3, "name": "Water Storage", "capacity": 150, "current_fill": 100, "location": "Module B"},
        {"id": 4, "name": "Oxygen Cabinet", "capacity": 50, "current_fill": 25, "location": "Airlock"},
        {"id": 5, "name": "Equipment Locker", "capacity": 80, "current_fill": 30, "location": "Lab Module"}
    ]

def default_logs():
    return [
        {
            "id": "log-1",
            "timestamp": "2025-04-01T10:30:00Z",
            "action": "Add",
            "item_id": 1,
            "quantity": 20,
            "user": "astronaut1"
        }
    ]

def default_waste():
    return [
        {
            "id": "waste-1",
            "name": "Used Medical Supplies",
            "weight": 5,
            "status": "identified",
            "return_plan": None
        }
    ]

# Initialize data
inventory_items = load_data(INVENTORY_FILE, default_inventory)
containers = load_data(CONTAINERS_FILE, default_containers)
logs = load_data(LOGS_FILE, default_logs)
waste_items = load_data(WASTE_FILE, default_waste)

# Add log entry
def add_log(action, item_id, quantity, user="system"):
    log_entry = {
        "id": f"log-{uuid.uuid4()}",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "action": action,
        "item_id": item_id,
        "quantity": quantity,
        "user": user
    }
    logs.append(log_entry)
    save_data(LOGS_FILE, logs)
    return log_entry

# Existing inventory endpoints
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
        "expiry_date": data.get("expiry_date", ""),
        "container_id": data.get("container_id", None)
    }
    
    inventory_items.append(new_item)
    save_data(INVENTORY_FILE, inventory_items)
    add_log("Add", new_id, data.get("quantity", 0))
    return jsonify(new_item), 201

@app.route('/api/inventory/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        return jsonify({"error": "Item not found"}), 404
        
    data = request.json
    if not data:
        return jsonify({"error": "Invalid data"}), 400
    
    old_quantity = item["quantity"]
    
    for key in data:
        if key in item and key != "id":  # Prevent ID changes
            item[key] = data[key]
    
    save_data(INVENTORY_FILE, inventory_items)
    
    if "quantity" in data and old_quantity != data["quantity"]:
        add_log("Update", item_id, data["quantity"] - old_quantity)
            
    return jsonify(item)

@app.route('/api/inventory/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    global inventory_items
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        return jsonify({"error": "Item not found"}), 404
    
    quantity = item["quantity"]
    inventory_items = [item for item in inventory_items if item["id"] != item_id]
    save_data(INVENTORY_FILE, inventory_items)
    add_log("Delete", item_id, -quantity)
    return jsonify({"message": "Item deleted successfully"})

# New API endpoints

# 1. Placement Recommendations API
@app.route('/api/placement', methods=['POST'])
def get_placement_recommendations():
    data = request.json
    if not data or 'item_type' not in data:
        return jsonify({"error": "Missing required field: item_type"}), 400
    
    item_type = data['item_type']
    quantity = data.get('quantity', 1)
    
    # Find containers with sufficient space
    suitable_containers = []
    for container in containers:
        if container['capacity'] - container['current_fill'] >= quantity:
            # Simple algorithm: score based on available space and location
            # More sophisticated algorithm could be implemented here
            score = (container['capacity'] - container['current_fill']) * 0.5
            
            # Boost score if container already has similar items
            similar_items = [item for item in inventory_items 
                            if item['container_id'] == container['id'] and item_type.lower() in item['name'].lower()]
            if similar_items:
                score += 20
                
            suitable_containers.append({
                "container_id": container['id'],
                "container_name": container['name'],
                "location": container['location'],
                "available_space": container['capacity'] - container['current_fill'],
                "score": score
            })
    
    # Sort by score descending
    suitable_containers.sort(key=lambda x: x['score'], reverse=True)
    
    # Return top 3 recommendations or all if less than 3
    recommendations = suitable_containers[:3] if len(suitable_containers) > 3 else suitable_containers
    
    return jsonify({
        "item_type": item_type,
        "quantity": quantity,
        "recommendations": recommendations
    })

# 2. Item Search API
@app.route('/api/search', methods=['GET'])
def search_items():
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    location = request.args.get('location', '')
    
    results = []
    for item in inventory_items:
        if (query.lower() in item['name'].lower() and
            (not category or category.lower() in item['name'].lower()) and
            (not location or location.lower() in item['location'].lower())):
            results.append(item)
    
    return jsonify({"results": results, "count": len(results)})

# Item Retrieve API
@app.route('/api/retrieve', methods=['POST'])
def retrieve_item():
    data = request.json
    if not data or 'item_id' not in data:
        return jsonify({"error": "Missing required field: item_id"}), 400
    
    item_id = data['item_id']
    quantity = data.get('quantity', 1)
    user = data.get('user', 'system')
    
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        return jsonify({"error": "Item not found"}), 404
    
    if item['quantity'] < quantity:
        return jsonify({"error": "Insufficient quantity available"}), 400
    
    # Update item quantity
    item['quantity'] -= quantity
    save_data(INVENTORY_FILE, inventory_items)
    
    # Update container fill level if applicable
    if item['container_id']:
        container = next((c for c in containers if c["id"] == item['container_id']), None)
        if container:
            container['current_fill'] -= quantity
            save_data(CONTAINERS_FILE, containers)
    
    # Log the retrieval
    add_log("Retrieve", item_id, -quantity, user)
    
    return jsonify({
        "success": True,
        "item_id": item_id,
        "name": item['name'],
        "quantity_retrieved": quantity,
        "remaining_quantity": item['quantity']
    })

# Item Place API
@app.route('/api/place', methods=['POST'])
def place_item():
    data = request.json
    if not data or 'item_id' not in data or 'container_id' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    item_id = data['item_id']
    container_id = data['container_id']
    quantity = data.get('quantity', 1)
    user = data.get('user', 'system')
    
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        return jsonify({"error": "Item not found"}), 404
    
    container = next((c for c in containers if c["id"] == container_id), None)
    if not container:
        return jsonify({"error": "Container not found"}), 404
    
    if container['capacity'] - container['current_fill'] < quantity:
        return jsonify({"error": "Container does not have enough space"}), 400
    
    # Update item
    item['quantity'] += quantity
    item['container_id'] = container_id
    item['location'] = container['location']
    
    # Update container
    container['current_fill'] += quantity
    
    # Save changes
    save_data(INVENTORY_FILE, inventory_items)
    save_data(CONTAINERS_FILE, containers)
    
    # Log the placement
    add_log("Place", item_id, quantity, user)
    
    return jsonify({
        "success": True,
        "item_id": item_id,
        "name": item['name'],
        "quantity_placed": quantity,
        "container": container['name'],
        "location": container['location']
    })

# 3. Waste Management API
@app.route('/api/waste/identify', methods=['POST'])
def identify_waste():
    data = request.json
    if not data or 'name' not in data or 'weight' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    waste_id = f"waste-{uuid.uuid4()}"
    new_waste = {
        "id": waste_id,
        "name": data['name'],
        "weight": data['weight'],
        "status": "identified",
        "return_plan": None
    }
    
    waste_items.append(new_waste)
    save_data(WASTE_FILE, waste_items)
    
    return jsonify({
        "success": True,
        "waste_id": waste_id,
        "status": "identified"
    })

@app.route('/api/waste/return-plan', methods=['POST'])
def waste_return_plan():
    data = request.json
    if not data or 'waste_id' not in data:
        return jsonify({"error": "Missing required field: waste_id"}), 400
    
    waste_id = data['waste_id']
    waste_item = next((w for w in waste_items if w["id"] == waste_id), None)
    if not waste_item:
        return jsonify({"error": "Waste item not found"}), 404
    
    # Generate a simple return plan
    return_plan = {
        "vehicle": "SpaceX Dragon",
        "scheduled_date": (datetime.datetime.utcnow() + datetime.timedelta(days=30)).strftime("%Y-%m-%d"),
        "storage_location": "Waste Bay Section C",
        "handling_instructions": "Secure in triple containment bag"
    }
    
    # Update waste item
    waste_item['status'] = "return-planned"
    waste_item['return_plan'] = return_plan
    save_data(WASTE_FILE, waste_items)
    
    return jsonify({
        "success": True,
        "waste_id": waste_id,
        "status": "return-planned",
        "return_plan": return_plan
    })

@app.route('/api/waste/complete-undocking', methods=['POST'])
def complete_waste_undocking():
    data = request.json
    if not data or 'waste_id' not in data:
        return jsonify({"error": "Missing required field: waste_id"}), 400
    
    waste_id = data['waste_id']
    waste_item = next((w for w in waste_items if w["id"] == waste_id), None)
    if not waste_item:
        return jsonify({"error": "Waste item not found"}), 404
    
    if waste_item['status'] != "return-planned":
        return jsonify({"error": "Waste item does not have a return plan"}), 400
    
    # Update waste item
    waste_item['status'] = "returned"
    waste_item['return_completion_date'] = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    save_data(WASTE_FILE, waste_items)
    
    return jsonify({
        "success": True,
        "waste_id": waste_id,
        "status": "returned",
        "completion_date": waste_item['return_completion_date']
    })

# 4. Time Simulation API
@app.route('/api/simulate/day', methods=['POST'])
def simulate_day():
    # Check for expired items
    expired_items = []
    today = datetime.datetime.utcnow()
    
    for item in inventory_items:
        if 'expiry_date' in item and item['expiry_date']:
            expiry_date = datetime.datetime.strptime(item['expiry_date'], "%Y-%m-%d")
            days_left = (expiry_date - today).days
            
            if days_left <= 0:
                expired_items.append({
                    "item_id": item['id'],
                    "name": item['name'],
                    "expiry_date": item['expiry_date'],
                    "status": "expired"
                })
            elif days_left <= 30:
                expired_items.append({
                    "item_id": item['id'],
                    "name": item['name'],
                    "expiry_date": item['expiry_date'],
                    "days_left": days_left,
                    "status": "expiring_soon"
                })
    
    # Simulate usage of consumables
    consumables_used = []
    for item in inventory_items:
        if "Food" in item['name'] or "Water" in item['name'] or "Medical" in item['name']:
            # Simulate random daily usage between 1-5% of quantity
            import random
            usage = max(1, int(item['quantity'] * random.uniform(0.01, 0.05)))
            
            if item['quantity'] >= usage:
                item['quantity'] -= usage
                consumables_used.append({
                    "item_id": item['id'],
                    "name": item['name'],
                    "used": usage,
                    "remaining": item['quantity']
                })
                
                # Log the usage
                add_log("Use", item['id'], -usage, "simulation")
    
    # Save changes
    save_data(INVENTORY_FILE, inventory_items)
    
    return jsonify({
        "success": True,
        "date_simulated": today.strftime("%Y-%m-%d"),
        "expired_items": expired_items,
        "consumables_used": consumables_used
    })

# 5. Import/Export API
@app.route('/api/import/items', methods=['POST'])
def import_items():
    data = request.json
    if not data or 'items' not in data:
        return jsonify({"error": "Missing required field: items"}), 400
    
    items = data['items']
    imported_count = 0
    new_items = []
    
    for item_data in items:
        if 'name' not in item_data or 'quantity' not in item_data:
            continue
        
        new_id = 1
        if inventory_items:
            new_id = max([item["id"] for item in inventory_items]) + 1
            
        new_item = {
            "id": new_id,
            "name": item_data['name'],
            "quantity": item_data['quantity'],
            "location": item_data.get('location', 'Receiving Bay'),
            "expiry_date": item_data.get('expiry_date', ''),
            "container_id": item_data.get('container_id', None)
        }
        
        inventory_items.append(new_item)
        new_items.append(new_item)
        imported_count += 1
        
        # Log the import
        add_log("Import", new_id, item_data['quantity'])
    
    save_data(INVENTORY_FILE, inventory_items)
    
    return jsonify({
        "success": True,
        "imported_count": imported_count,
        "items": new_items
    })

@app.route('/api/import/containers', methods=['POST'])
def import_containers():
    data = request.json
    if not data or 'containers' not in data:
        return jsonify({"error": "Missing required field: containers"}), 400
    
    container_data = data['containers']
    imported_count = 0
    new_containers = []
    
    for container in container_data:
        if 'name' not in container or 'capacity' not in container:
            continue
        
        new_id = 1
        if containers:
            new_id = max([c["id"] for c in containers]) + 1
            
        new_container = {
            "id": new_id,
            "name": container['name'],
            "capacity": container['capacity'],
            "current_fill": container.get('current_fill', 0),
            "location": container.get('location', 'Receiving Bay')
        }
        
        containers.append(new_container)
        new_containers.append(new_container)
        imported_count += 1
    
    save_data(CONTAINERS_FILE, containers)
    
    return jsonify({
        "success": True,
        "imported_count": imported_count,
        "containers": new_containers
    })

@app.route('/api/export/arrangement', methods=['GET'])
def export_arrangement():
    # Build comprehensive data structure of current arrangement
    export_data = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "containers": containers,
        "inventory": inventory_items,
        "storage_stats": {
            "total_containers": len(containers),
            "total_items": len(inventory_items),
            "total_capacity": sum(c['capacity'] for c in containers),
            "total_used": sum(c['current_fill'] for c in containers),
            "utilization_percentage": 
                round(sum(c['current_fill'] for c in containers) / 
                      sum(c['capacity'] for c in containers) * 100 
                      if sum(c['capacity'] for c in containers) > 0 else 0, 2)
        }
    }
    
    return jsonify(export_data)

# 6. Logging API
@app.route('/api/logs', methods=['GET'])
def get_logs():
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    action_type = request.args.get('action', '')
    user = request.args.get('user', '')
    
    filtered_logs = logs
    
    if start_date:
        try:
            start = datetime.datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            filtered_logs = [log for log in filtered_logs 
                             if datetime.datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')) >= start]
        except:
            pass
    
    if end_date:
        try:
            end = datetime.datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            filtered_logs = [log for log in filtered_logs 
                             if datetime.datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')) <= end]
        except:
            pass
    
    if action_type:
        filtered_logs = [log for log in filtered_logs if log['action'] == action_type]
    
    if user:
        filtered_logs = [log for log in filtered_logs if log['user'] == user]
    
    return jsonify({
        "count": len(filtered_logs),
        "logs": filtered_logs
    })

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
