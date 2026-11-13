
import os
import mysql.connector
from mysql.connector import Error
from datetime import date, timedelta
from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, abort
)

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "easybus-demo-secret")

SOURCE = "Hyderabad"

DESTINATIONS = [
    "Visakhapatnam",
    "Vijayawada",
    "Sompeta",
    "Baruva"
]


# ==========================================
# AWS RDS MYSQL CONNECTION
# ==========================================

def get_db():
    return mysql.connector.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "3306")),
        database=os.environ.get("DB_NAME", "busbooking"),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connection_timeout=10
    )


# ==========================================
# CREATE DATABASE TABLES AND SAMPLE BUSES
# ==========================================

def init_db():

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS buses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                bus_name VARCHAR(100) NOT NULL,
                source VARCHAR(100) NOT NULL,
                destination VARCHAR(100) NOT NULL,
                journey_date DATE NOT NULL,
                departure_time VARCHAR(10) NOT NULL,
                arrival_time VARCHAR(10) NOT NULL,
                fare DECIMAL(10,2) NOT NULL,
                total_seats INT NOT NULL,
                available_seats INT NOT NULL
            ) ENGINE=InnoDB
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                bus_id INT NOT NULL,
                passenger_name VARCHAR(150) NOT NULL,
                email VARCHAR(255) NOT NULL,
                phone VARCHAR(30) NOT NULL,
                seats INT NOT NULL,
                total_amount DECIMAL(10,2) NOT NULL,
                payment_method VARCHAR(30) NOT NULL,
                payment_status VARCHAR(50) NOT NULL,
                booking_status VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_booking_bus
                    FOREIGN KEY (bus_id) REFERENCES buses(id)
            ) ENGINE=InnoDB
        """)

        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM buses")
        count = cursor.fetchone()[0]

        if count == 0:

            destination_fares = {
                "Visakhapatnam": 1200,
                "Vijayawada": 650,
                "Sompeta": 1400,
                "Baruva": 1500
            }

            bus_options = [
                ("Orange Travels", "21:00", "05:00", 0, 40),
                ("VRL Travels", "22:00", "06:00", 100, 36),
                ("Kaveri Travels", "20:30", "04:30", 150, 40)
            ]

            insert_query = """
                INSERT INTO buses (
                    bus_name, source, destination,
                    journey_date, departure_time, arrival_time,
                    fare, total_seats, available_seats
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            for day in range(30):

                travel_date = date.today() + timedelta(days=day)

                for destination, base_fare in destination_fares.items():

                    for bus_name, departure, arrival, extra, seats in bus_options:

                        fare = base_fare + extra

                        cursor.execute(insert_query, (
                            bus_name,
                            SOURCE,
                            destination,
                            travel_date,
                            departure,
                            arrival,
                            fare,
                            seats,
                            seats
                        ))

            conn.commit()

    finally:
        cursor.close()
        conn.close()


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def home():

    return render_template(
        "index.html",
        source=SOURCE,
        destinations=DESTINATIONS,
        today=date.today().isoformat()
    )


# ==========================================
# SEARCH BUSES
# ==========================================

@app.route("/search", methods=["GET", "POST"])
def search_buses():

    if request.method == "GET":
        return redirect(url_for("home"))

    source = request.form.get("source", SOURCE).strip()
    destination = request.form.get("destination", "").strip()
    journey_date = request.form.get("journey_date", "").strip()

    if source.lower() != SOURCE.lower():
        flash("Starting point must be Hyderabad.")
        return redirect(url_for("home"))

    if destination not in DESTINATIONS:
        flash("Please select a valid destination.")
        return redirect(url_for("home"))

    try:
        selected_date = date.fromisoformat(journey_date)

        if selected_date < date.today():
            flash("Please select today or a future date.")
            return redirect(url_for("home"))

    except ValueError:
        flash("Please select a valid journey date.")
        return redirect(url_for("home"))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT *
            FROM buses
            WHERE LOWER(source) = LOWER(%s)
              AND LOWER(destination) = LOWER(%s)
              AND journey_date = %s
              AND available_seats > 0
            ORDER BY departure_time
        """, (SOURCE, destination, journey_date))

        buses = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    return render_template(
        "search_results.html",
        buses=buses,
        source=SOURCE,
        destination=destination,
        journey_date=journey_date
    )


# ==========================================
# BOOK TICKETS
# ==========================================

@app.route("/book/<int:bus_id>", methods=["GET", "POST"])
def book_bus(bus_id):

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT * FROM buses WHERE id = %s",
            (bus_id,)
        )
        bus = cursor.fetchone()

        if bus is None:
            abort(404)

        if request.method == "POST":

            passenger_name = request.form.get(
                "passenger_name", ""
            ).strip()

            email = request.form.get("email", "").strip()
            phone = request.form.get("phone", "").strip()

            try:
                seats = int(request.form.get("seats", "1"))
            except ValueError:
                seats = 0

            if not passenger_name or not email or not phone:
                flash("Please fill all passenger details.")
                return redirect(url_for("book_bus", bus_id=bus_id))

            if seats < 1 or seats > 6:
                flash("You can book between 1 and 6 seats.")
                return redirect(url_for("book_bus", bus_id=bus_id))

            if seats > bus["available_seats"]:
                flash(
                    "Only {} seats are available.".format(
                        bus["available_seats"]
                    )
                )
                return redirect(url_for("book_bus", bus_id=bus_id))

            total_amount = seats * float(bus["fare"])

            cursor.execute("""
                INSERT INTO bookings (
                    bus_id, passenger_name, email, phone,
                    seats, total_amount, payment_method,
                    payment_status, booking_status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                bus_id,
                passenger_name,
                email,
                phone,
                seats,
                total_amount,
                "NOT_SELECTED",
                "NOT_PAID",
                "AWAITING_PAYMENT"
            ))

            booking_id = cursor.lastrowid
            conn.commit()

            return redirect(url_for("payment", booking_id=booking_id))

    finally:
        cursor.close()
        conn.close()

    return render_template("book.html", bus=bus)


# ==========================================
# PAYMENT PAGE
# ==========================================

@app.route("/payment/<int:booking_id>", methods=["GET", "POST"])
def payment(booking_id):

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                bookings.*,
                buses.bus_name,
                buses.source,
                buses.destination,
                buses.journey_date,
                buses.departure_time,
                buses.available_seats
            FROM bookings
            JOIN buses ON bookings.bus_id = buses.id
            WHERE bookings.id = %s
        """, (booking_id,))

        booking = cursor.fetchone()

        if booking is None:
            abort(404)

        if booking["booking_status"] == "CONFIRMED":
            return render_template(
                "booking_success.html",
                booking=booking
            )

        if request.method == "POST":

            payment_method = request.form.get(
                "payment_method", ""
            ).upper()

            allowed_methods = ["UPI", "CARD", "CASH"]

            if payment_method not in allowed_methods:
                flash("Please select a valid payment method.")
                return redirect(url_for("payment", booking_id=booking_id))

            try:
                conn.start_transaction()

                # Lock this booking while confirming it
                cursor.execute("""
                    SELECT *
                    FROM bookings
                    WHERE id = %s
                    FOR UPDATE
                """, (booking_id,))

                current_booking = cursor.fetchone()

                if current_booking is None:
                    conn.rollback()
                    abort(404)

                if current_booking["booking_status"] == "CONFIRMED":
                    conn.commit()
                    return redirect(url_for("payment", booking_id=booking_id))

                # Reduce seats only if enough seats are available
                cursor.execute("""
                    UPDATE buses
                    SET available_seats = available_seats - %s
                    WHERE id = %s
                      AND available_seats >= %s
                """, (
                    current_booking["seats"],
                    current_booking["bus_id"],
                    current_booking["seats"]
                ))

                if cursor.rowcount != 1:
                    conn.rollback()
                    return "Sorry, requested seats are no longer available.", 409

                if payment_method == "CASH":
                    payment_status = "PAY_ON_BOARD"
                else:
                    # Demo only. No real payment is processed.
                    payment_status = "DEMO_PAID"

                cursor.execute("""
                    UPDATE bookings
                    SET payment_method = %s,
                        payment_status = %s,
                        booking_status = 'CONFIRMED'
                    WHERE id = %s
                """, (
                    payment_method,
                    payment_status,
                    booking_id
                ))

                conn.commit()

            except Error:
                conn.rollback()
                app.logger.exception("Booking payment update failed")
                return "Booking failed. Please try again.", 500

            return redirect(url_for("payment", booking_id=booking_id))

    finally:
        cursor.close()
        conn.close()

    return render_template("payment.html", booking=booking)


# ==========================================
# BOOKING HISTORY
# ==========================================

@app.route("/my-bookings")
def my_bookings():

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                bookings.*,
                buses.bus_name,
                buses.source,
                buses.destination,
                buses.journey_date,
                buses.departure_time
            FROM bookings
            JOIN buses ON bookings.bus_id = buses.id
            ORDER BY bookings.id DESC
        """)

        bookings = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    return render_template(
        "my_bookings.html",
        bookings=bookings
    )


# ==========================================
# DATABASE HEALTH CHECK
# ==========================================

@app.route("/health", methods=["GET"])
def health():

    return {
        "status": "healthy",
        "application": "EasyBus"
    }, 200


@app.route("/test-db", methods=["GET"])
def test_db():

    conn = None

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()

        return {
            "status": "success",
            "message": "AWS RDS MySQL Connected Successfully!"
        }, 200

    except Error:
        app.logger.exception("RDS connection test failed")
        return {
            "status": "error",
            "message": "Could not connect to AWS RDS MySQL"
        }, 500

    finally:
        if conn and conn.is_connected():
            conn.close()


# ==========================================
# INITIALIZE DATABASE
# ==========================================

init_db()


# ==========================================
# START APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
