import os
from datetime import datetime # --- NEW --- Import datetime to handle dates
from flask import Flask, jsonify, request
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

    # --- NEW --- This line creates the "one-to-many" relationship back to Booking
    bookings = db.relationship('Booking', backref='room', lazy=True)

    def __repr__(self):
        return f'<Room {self.name}>'

# --- NEW --- This is the entire new Booking model class
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guest_name = db.Column(db.String(100), nullable=False)
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    num_adults = db.Column(db.Integer, nullable=False, default=1)
    num_children = db.Column(db.Integer, nullable=False, default=0)
    phone_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    
    # Payment & Status
    booking_status = db.Column(db.String(20), nullable=False, default='Confirmed')
    payment_status = db.Column(db.String(20), nullable=False, default='Unpaid')
    total_amount = db.Column(db.Float, nullable=True)
    amount_paid = db.Column(db.Float, nullable=True, default=0.0)
    payment_method = db.Column(db.String(20), nullable=True)
    
    # The Relationship (Foreign Key)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)

    def __repr__(self):
        return f'<Booking for {self.guest_name} in Room {self.room_id}>'


# --- API ROUTES ---

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({"status": "ok", "message": "Server is running"})

# --- Room CRUD Endpoints ---

@app.route('/api/rooms', methods=['POST'])
def create_room():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'message': 'Room name is required'}), 400
    new_room = Room(name=data['name'], status=data.get('status', 'Available'))
    db.session.add(new_room)
    db.session.commit()
    return jsonify({'message': 'Room created successfully', 'room': {'id': new_room.id, 'name': new_room.name, 'status': new_room.status}}), 201

@app.route('/api/rooms', methods=['GET'])
def get_all_rooms():
    rooms = Room.query.order_by(Room.id).all()
    output = []
    for room in rooms:
        room_data = {'id': room.id, 'name': room.name, 'status': room.status}
        output.append(room_data)
    return jsonify({'rooms': output})

@app.route('/api/rooms/<int:room_id>', methods=['PUT'])
def update_room(room_id):
    room = Room.query.get_or_404(room_id)
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No input data provided'}), 400
    room.name = data.get('name', room.name)
    room.status = data.get('status', room.status)
    db.session.commit()
    return jsonify({'message': 'Room updated successfully', 'room': {'id': room.id, 'name': room.name, 'status': room.status}})

@app.route('/api/rooms/<int:room_id>', methods=['DELETE'])
def delete_room(room_id):
    room = Room.query.get_or_404(room_id)
    db.session.delete(room)
    db.session.commit()
    return jsonify({'message': 'Room deleted successfully'})

# --- Booking CRUD Endpoints ---

@app.route('/api/bookings', methods=['POST'])
def create_booking():
    """
    This endpoint creates a new booking.
    """
    data = request.get_json()

    # 1. Validation: Check for required fields
    required_fields = ['guest_name', 'check_in_date', 'check_out_date', 'room_id']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400

    # 2. Date Conversion: Convert string dates from JSON to Python Date objects
    try:
        check_in = datetime.strptime(data['check_in_date'], '%Y-%m-%d').date()
        check_out = datetime.strptime(data['check_out_date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'message': 'Invalid date format. Please use YYYY-MM-DD.'}), 400

    # 3. Validation: Check if the room exists
    room_to_book = Room.query.get(data['room_id'])
    if not room_to_book:
        return jsonify({'message': 'Room not found with the provided ID'}), 404

    # Note: For a real-world app, we'd also add logic here to check
    # if the room is already booked for these dates. We'll add that later.

    # 4. Create the new Booking object
    new_booking = Booking(
        guest_name=data['guest_name'],
        check_in_date=check_in,
        check_out_date=check_out,
        room_id=data['room_id'],
        num_adults=data.get('num_adults', 1),
        num_children=data.get('num_children', 0),
        phone_number=data.get('phone_number'),
        email=data.get('email')
        # We can leave payment details to be updated later
    )

    # 5. Save to the database
    db.session.add(new_booking)
    db.session.commit()

    # 6. Return a success response
    return jsonify({'message': 'Booking created successfully', 'booking_id': new_booking.id}), 201

@app.route('/api/bookings', methods=['GET'])
def get_all_bookings():
    """
    This endpoint returns a list of all bookings.
    """
    bookings = Booking.query.order_by(Booking.check_in_date).all()
    output = []
    for booking in bookings:
        # Here we use the back-reference 'room' to get the room's name!
        booking_data = {
            'id': booking.id,
            'guest_name': booking.guest_name,
            'check_in_date': booking.check_in_date.strftime('%Y-%m-%d'),
            'check_out_date': booking.check_out_date.strftime('%Y-%m-%d'),
            'room_id': booking.room_id,
            'room_name': booking.room.name  # The power of relationships!
        }
        output.append(booking_data)
        
    return jsonify({'bookings': output})

# --- This block allows you to run the app directly ---
if __name__ == '__main__':
    app.run(debug=True)