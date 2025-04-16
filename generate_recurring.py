from app import create_app, db
from app.models import RecurringService, Reservation
from datetime import datetime, timedelta

app = create_app()

def generate_reservations():
    today = datetime.today().date()
    upcoming = today + timedelta(days=5)

    recurring_services = RecurringService.query.filter_by(status="active").all()
    
    if not recurring_services:
        print("ℹ️ No active recurring services found.")
        return

    for r in recurring_services:
        # No crear si ya existe una reserva para esa fecha
        existing = Reservation.query.filter_by(date=upcoming, recurring_id=r.id).first()
        if existing:
            continue

        new_reservation = Reservation(
            user_id=r.user_id,
            service_type=r.service_type,
            date=upcoming,
            time=r.time,
            address=r.address,
            notes=r.notes,
            lat=r.lat,
            lng=r.lng,
            status="pending",
            recurring_id=r.id
        )
        db.session.add(new_reservation)

    db.session.commit()
    print("✔️ Reservaciones generadas exitosamente.")

# 🔄 Ejecutar dentro del contexto Flask
if __name__ == "__main__":
    with app.app_context():
        generate_reservations()
