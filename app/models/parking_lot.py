# app/models/parking_lot.py

from app import db

class ParkingLot(db.Model):
    __tablename__ = 'parking_lot'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(150), nullable=False)
    pin = db.Column(db.Integer, nullable=True)
    rate = db.Column(db.Integer, nullable=False)
   
    spots = db.relationship('ParkingSpot', backref='lot', lazy=True, cascade='all, delete-orphan')
