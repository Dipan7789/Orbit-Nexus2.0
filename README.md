# Orbit-Nexus2.0
Starring Dipan Chakraborty , Sudutta Mukherjee

# ISS Inventory Management System

## Overview
This project is a comprehensive inventory management system designed for the International Space Station. It provides tools for tracking supplies, managing storage locations, and optimizing resource utilization in space.

## Features
- Real-time inventory tracking
- Storage optimization algorithms
- Expiry date management
- Import/export functionality
- Interactive storage visualization
- User authentication and role-based access

## Tech Stack
- **Frontend**: React, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: Flask (Python)
- **Data Format**: JSON
- **Containerization**: Docker

## Getting Started

### Prerequisites
- Docker

### Running the Application

#### Using Docker
1. Clone the repository:
   ```
   git clone https://github.com/orbit-nexus/iss-inventory-system.git
   cd iss-inventory-system
   ```

2. Build and run the Docker container:
   ```
   docker build -t iss-inventory-system .
   docker run -p 8000:8000 -v $(pwd)/data:/app/data iss-inventory-system
   ```

3. Access the application at `http://localhost:8000`

#### Development Setup
1. Frontend Development:
   ```
   npm install
   npm run dev
   ```

2. Backend Development:
   ```
   pip install -r requirements.txt
   python app.py
   ```

## API Endpoints
- `GET /api/inventory` - Get all inventory items
- `GET /api/inventory/<item_id>` - Get specific inventory item
- `POST /api/inventory` - Add new inventory item
- `PUT /api/inventory/<item_id>` - Update an inventory item
- `DELETE /api/inventory/<item_id>` - Delete an inventory item

## License
ISS Inventory Management System is MIT licensed.
