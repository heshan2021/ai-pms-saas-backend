import os
from flask import Flask, jsonify, request # Combined imports here
from flask_sqlalchemy import SQLAlchemy

# Initialize the Flask application
app = Flask(__name__)

# --- DATABASE CONFIGURATION ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'pms.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database extension
db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=False, default='Available')

    def __repr__(self):
        return f'<Room {self.name}>'

# --- API ROUTES ---

# This is the first API route function
@app.route('/api/status', methods=['GET'])
def get_status():
    """
    This endpoint returns the current status of the API.
    """
    return jsonify({"status": "ok", "message": "Server is running"})

# This is the SECOND, SEPARATE API route function
@app.route('/api/rooms', methods=['POST'])
def create_room():
    """
    This endpoint creates a new room.
    """
    data = request.get_json()

    if not data or 'name' not in data:
        return jsonify({'message': 'Room name is required'}), 400

    new_room = Room(name=data['name'], status=data.get('status', 'Available'))

    db.session.add(new_room)
    db.session.commit()

    return jsonify({'message': 'Room created successfully', 'room': {'id': new_room.id, 'name': new_room.name, 'status': new_room.status}}), 201

@app.route('/api/rooms', methods=['GET'])
def get_all_rooms():
    """
    This endpoint returns a list of all rooms in the database.
    """
    # Query the database to get all rooms, ordered by their ID
    rooms = Room.query.order_by(Room.id).all()
    
    # Create a list of dictionaries from the room objects
    output = []
    for room in rooms:
        room_data = {
            'id': room.id,
            'name': room.name,
            'status': room.status
        }
        output.append(room_data)
        
    # Return the list of rooms as a JSON response
    return jsonify({'rooms': output})

@app.route('/api/rooms/<int:room_id>', methods=['PUT'])
def update_room(room_id):
    """
    This endpoint updates the details of a specific room.
    """
    # --- DEBUGGING STARTS HERE ---
    print(f"--- Attempting to update room with ID: {room_id} ---")
    print(f"Type of ID received: {type(room_id)}")
    
    room = Room.query.get(room_id) # Using .get() instead of get_or_404 for now
    
    print(f"Result from database query: {room}")
    # --- DEBUGGING ENDS HERE ---

    if not room:
        return jsonify({'message': 'Room not found with that ID'}), 404

    data = request.get_json()

    if not data:
        return jsonify({'message': 'No input data provided'}), 400

    room.name = data.get('name', room.name)
    room.status = data.get('status', room.status)
    
    db.session.commit()
    
    return jsonify({'message': 'Room updated successfully', 'room': {'id': room.id, 'name': room.name, 'status': room.status}})

@app.route('/api/rooms/<int:room_id>', methods=['DELETE'])
def delete_room(room_id):
    """
    This endpoint deletes a specific room from the database.
    """
    # Find the specific room, or return a 404 if it's not found
    room = Room.query.get_or_404(room_id)
    
    # Delete the room from the database session
    db.session.delete(room)
    
    # Commit the change to make it permanent
    db.session.commit()
    
    # Return a success message
    return jsonify({'message': 'Room deleted successfully'})

# --- This block allows you to run the app directly ---
if __name__ == '__main__':
    app.run(debug=True)