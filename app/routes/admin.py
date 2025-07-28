# app/routes/admin.py
from app.models.user import User  
from app.models import ParkingLot, ParkingSpot, ParkingRecord
from app import db
from flask import Blueprint, render_template, session, redirect, url_for, request, flash

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/base')
def base():
    return render_template('admin_base.html')

@admin_bp.route('/')
def home():
    lots = ParkingLot.query.all()
    parking_lots = []

    for lot in lots:
        # Get all spots related to this lot
        spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()

        # Add parking record reference if the spot is occupied
        for spot in spots:
            if not spot.is_available:
                spot.record = ParkingRecord.query.filter_by(spot_id=spot.id, end_time=None).first()
            else:
                spot.record = None

        # Add extra computed values directly to the model
        lot.spots = spots
        lot.occupied_count = sum(1 for s in spots if not s.is_available)
        lot.total_spots = len(spots)

        # Append the full lot object
        parking_lots.append(lot)

    return render_template('admin_home.html', parking_lots=parking_lots)

@admin_bp.route('/users')
def users():
    # Get all users (no role filtering needed since users table only has regular users)
    all_users = User.query.all()
    return render_template('admin_users.html', users=all_users)

@admin_bp.route('/search', methods=['GET'])
def search():
    search_by = request.args.get('search_by')
    query = request.args.get('query')
    results = None

    if search_by and query:

        if search_by == 'user_id':
            if query.isdigit():
                user_id = int(query)
                results = ParkingRecord.query.filter_by(user_id=user_id).all()
            else:
                results = []

        elif search_by == 'parking_lot':
            lots = ParkingLot.query.filter(ParkingLot.name.ilike(f"%{query}%")).all()
            results = []

            for lot in lots:
                spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()

                for spot in spots:
                    if not spot.is_available:
                        spot.record = ParkingRecord.query.filter_by(spot_id=spot.id, end_time=None).first()
                    else:
                        spot.record = None

                lot.spots = spots
                lot.occupied_count = sum(not s.is_available for s in spots)
                lot.total_spots = len(spots)

                results.append(lot)

        elif search_by == 'parking_spot':
            if query.isdigit():
                spot_id = int(query)
                spot = ParkingSpot.query.get(spot_id)

                if spot:
                    spot.lot = ParkingLot.query.get(spot.lot_id)
                    if not spot.is_available:
                        spot.record = ParkingRecord.query.filter_by(spot_id=spot.id, end_time=None).first()

                results = spot
            else:
                results = None

    return render_template("admin_search.html", search_by=search_by, query=query, results=results)


@admin_bp.route('/edit/<int:lot_id>', methods=['POST'])
def edit_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)

    # Get form values
    new_name = request.form['name']
    new_address = request.form['address']
    new_pin = request.form['pin']
    new_rate = float(request.form['rate'])
    new_total_spots = int(request.form['max_spots'])

    # Update basic fields
    lot.name = new_name
    lot.address = new_address
    lot.pin = new_pin
    lot.rate = new_rate

    # Adjust parking spots
    current_spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
    current_count = len(current_spots)

    if new_total_spots > current_count:
        # Add new empty spots
        for i in range(current_count + 1, new_total_spots + 1):
            new_spot = ParkingSpot(
                lot_id=lot.id,
                spot_number=f"S{i:03}",
                is_available=True
            )
            db.session.add(new_spot)
    elif new_total_spots < current_count:
        # Remove extra spots (only if available)
        removable_spots = [s for s in current_spots if s.is_available]
        to_remove = current_count - new_total_spots

        if len(removable_spots) < to_remove:
            flash("Cannot reduce max spots — too many spots are occupied.", "danger")
            return redirect(url_for('admin.home'))

        for spot in removable_spots[:to_remove]:
            db.session.delete(spot)

    # Finally update total_spots
    lot.total_spots = new_total_spots

    db.session.commit()
    flash("Parking lot updated successfully.", "success")
    return redirect(url_for('admin.home'))

@admin_bp.route('/add', methods=['POST'])
def add_lot():
    # Check if admin is logged in
    if session.get('role') != 'admin':
        flash("You must be admin to add parking lots.", "danger")
        return redirect(url_for('admin.home'))
    
    # Get data from form
    name = request.form.get('name')
    address = request.form.get('address')
    pin = request.form.get('pin')
    rate = request.form.get('rate')
    max_spots = request.form.get('max_spots')
    
    # Check if all fields are filled
    if not name or not address or not pin or not rate or not max_spots:
        flash("Please fill all fields.", "danger")
        return redirect(url_for('admin.home'))
    
    # Convert rate and max_spots to numbers
    try:
        rate = float(rate)
        max_spots = int(max_spots)
    except:
        flash("Rate and max spots must be valid numbers.", "danger")
        return redirect(url_for('admin.home'))
    
    # Create new parking lot
    new_lot = ParkingLot(name=name, address=address, pin=pin, rate=rate)
    db.session.add(new_lot)
    db.session.commit()
    
    # Create parking spots for this lot
    for i in range(1, max_spots + 1):
        spot = ParkingSpot(
            lot_id=new_lot.id,
            spot_number=f"S{i:03}",
            is_available=True
        )
        db.session.add(spot)
    
    db.session.commit()
    
    flash(f"Parking lot '{name}' added with {max_spots} spots!", "success")
    return redirect(url_for('admin.home'))

@admin_bp.route('/delete_lot/<int:lot_id>', methods=['POST'])
def delete_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)

    # Get all spots for this lot from database
    spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
    
    # Check for occupied spots
    occupied_spots = [spot for spot in spots if not spot.is_available]
    
    if occupied_spots:
        occupied_count = len(occupied_spots)
        if occupied_count == 1:
            flash(f"Cannot delete lot - there is 1 occupied spot.", "danger")
        else:
            flash(f"Cannot delete lot - there are {occupied_count} occupied spots.", "danger")
        return redirect(url_for('admin.home'))

    # If no occupied spots, safe to delete
    # First delete all spots associated with this lot
    for spot in spots:
        db.session.delete(spot)
    
    # Then delete the lot
    db.session.delete(lot)
    db.session.commit()
    
    flash(f"Parking lot '{lot.name}' deleted successfully.", "success")
    return redirect(url_for('admin.home'))

@admin_bp.route('/delete-spot/<int:spot_id>', methods=['POST'])
def delete_spot(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    db.session.delete(spot)
    db.session.commit()
    return redirect(url_for('admin.home'))

@admin_bp.route('/summary')
def summary():
    lots = ParkingLot.query.all()
    
    # Data for parking status chart
    labels = []
    available_data = []
    occupied_data = []
    
    # Data for revenue calculations
    revenue_data = []
    total_revenue = 0
    
    for lot in lots:
        # Get spots for this lot
        spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
        total_spots = len(spots)
        occupied = sum(1 for s in spots if not s.is_available)
        available = total_spots - occupied
        
        # Add to chart data
        labels.append(lot.name)
        available_data.append(available)
        occupied_data.append(occupied)
        
        # Calculate revenue for this lot
        records = ParkingRecord.query.join(ParkingSpot).filter(
            ParkingSpot.lot_id == lot.id,
            ParkingRecord.end_time.isnot(None)  # Only completed bookings
        ).all()
        
        lot_revenue = 0
        for record in records:
            if record.end_time:
                hours = (record.end_time - record.start_time).total_seconds() / 3600
                cost = round(hours * lot.rate, 2)
                lot_revenue += cost
        
        revenue_data.append({
            'name': lot.name,
            'total_revenue': lot_revenue
        })
        total_revenue += lot_revenue
    
    # Calculate summary stats
    total_available = sum(available_data)
    total_occupied = sum(occupied_data)
    total_spots_all = total_available + total_occupied
    occupancy_rate = round((total_occupied / total_spots_all * 100) if total_spots_all > 0 else 0, 2)
    
    earnings_summary = {
        'total': total_revenue
    }
    
    return render_template("admin_summary.html",
                         labels=labels,
                         available_data=available_data,
                         occupied_data=occupied_data,
                         revenue_data=revenue_data,
                         earnings_summary=earnings_summary,
                         total_available=total_available,
                         total_occupied=total_occupied,
                         occupancy_rate=occupancy_rate)