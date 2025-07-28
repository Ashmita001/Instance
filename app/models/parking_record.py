from datetime import datetime
from app import db

class ParkingRecord(db.Model):
    __tablename__ = 'parking_record'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'))
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'))
    vehicle_no = db.Column(db.String(20))
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='parked')  
    charge = db.Column(db.Float, default=0.0)
    
    lot = db.relationship('ParkingLot', backref='records')
    user = db.relationship('User', backref='parking_records')