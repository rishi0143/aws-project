
import os
import sqlite3
from datetime import date, timedelta
from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, abort
)

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY", "easybus-demo-secret"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "easybus.db")

SOURCE = "Hyderabad"

DESTINATIONS = [
    "Visakhapatnam",
    "Vijayawada",
    "Sompeta",
    "Baruva"
]


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_db():
    conn = sqlite3.connect(DATABASE, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ==========================================
# CREATE DATABASE AND TABLES
# ==========================================

def init_db():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS buses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bus_name TEXT NOT NULL,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            journey_date TEXT NOT NULL,
            departure_time TEXT NOT NULL,
            arrival_time TEXT NOT NULL,
            fare REAL NOT NULL,
            total_seats INTEGER NOT NULL,
            available_seats INTEGER NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bus_id INTEGER NOT NULL,
            passenger_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            seats INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            payment_method TEXT NOT NULL,
            payment_status TEXT NOT NULL,
            booking_status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(bus_id) REFERENCES buses(id)
        )
    """)

    conn.commit()

    # Insert sample buses if database is empty
    count = conn.execute(
        "SELECT COUNT(*) FROM buses"
    ).fetchone()[0]

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

        for day in range(30):

            travel_date = (
                date.today() + timedelta(days=day)
            ).isoformat()

            for destination, base_fare in destination_fares.items():

                for bus_name, departure, arrival, extra, seats in bus_options:

                    fare = base_fare + extra

                    conn.execute("""
                        INSERT INTO buses (
                            bus_name,
                            source,
                            destination,
                            journey_date,
                            departure_time,
                            arrival_time,
                            fare,
                            total_seats,
                            available_seats
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
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
# GET REQUEST FIXED
# ==========================================

@app.route("/search", methods=["GET", "POST"])
def search_buses():

    # Prevent HTTP 405 when opening /search directly
    if request.method == "GET":
        return redirect(url_for("home"))

    source = request.form.get(
        "source", SOURCE
    ).strip()

    destination = request.form.get(
        "destination", ""
    ).strip()

    journey_date = request.form.get(
        "journey_date", ""
    ).strip()

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

    buses = conn.execute("""
        SELECT *
        FROM buses
        WHERE LOWER(source) = LOWER(?)
        AND LOWER(destination) = LOWER(?)
        AND journey_date = ?
        AND available_seats > 0
        ORDER BY departure_time
    """, (
        SOURCE,
        destination,
        journey_date
    )).fetchall()

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

    bus = conn.execute(
        "SELECT * FROM buses WHERE id = ?",
        (bus_id,)
    ).fetchone()

    if bus is None:
        conn.close()
        abort(404)

    if request.method == "POST":

        passenger_name = request.form.get(
            "passenger_name", ""
        ).strip()

        email = request.form.get(
            "email", ""
        ).strip()

        phone = request.form.get(
            "phone", ""
        ).strip()

        try:
            seats = int(request.form.get("seats", "1"))
        except ValueError:
            seats = 0

        if not passenger_name or not email or not phone:

            conn.close()
            flash("Please fill all passenger details.")
            return redirect(
                url_for("book_bus", bus_id=bus_id)
            )

        if seats < 1 or seats > 6:

            conn.close()
            flash("You can book between 1 and 6 seats.")
            return redirect(
                url_for("book_bus", bus_id=bus_id)
            )

        if seats > bus["available_seats"]:

            conn.close()
            flash(
                "Only {} seats are available.".format(
                    bus["available_seats"]
                )
            )

            return redirect(
                url_for("book_bus", bus_id=bus_id)
            )

        total_amount = seats * bus["fare"]

        cursor = conn.execute("""
            INSERT INTO bookings (
                bus_id,
                passenger_name,
                email,
                phone,
                seats,
                total_amount,
                payment_method,
                payment_status,
                booking_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        conn.close()

        return redirect(
            url_for("payment", booking_id=booking_id)
        )

    conn.close()

    return render_template(
        "book.html",
        bus=bus
    )


# ==========================================
# PAYMENT PAGE
# ==========================================

@app.route(
    "/payment/<int:booking_id>",
    methods=["GET", "POST"]
)
def payment(booking_id):

    conn = get_db()

    booking = conn.execute("""
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
        WHERE bookings.id = ?
    """, (booking_id,)).fetchone()

    if booking is None:

        conn.close()
        abort(404)

    if booking["booking_status"] == "CONFIRMED":

        conn.close()

        return render_template(
            "booking_success.html",
            booking=booking
        )

    if request.method == "POST":

        payment_method = request.form.get(
            "payment_method", ""
        ).upper()

        allowed_methods = [
            "UPI",
            "CARD",
            "CASH"
        ]

        if payment_method not in allowed_methods:

            conn.close()
            flash("Please select a valid payment method.")

            return redirect(
                url_for("payment", booking_id=booking_id)
            )

        try:

            # Lock database while checking and updating seats
            conn.execute("BEGIN IMMEDIATE")

            # Check current booking status
            current_booking = conn.execute("""
                SELECT * FROM bookings
                WHERE id = ?
            """, (booking_id,)).fetchone()

            if current_booking is None:
                conn.rollback()
                conn.close()
                abort(404)

            if current_booking["booking_status"] == "CONFIRMED":
                conn.rollback()
                conn.close()
                return redirect(
                    url_for("payment", booking_id=booking_id)
                )

            # Reduce available seats only if sufficient seats exist
            result = conn.execute("""
                UPDATE buses
                SET available_seats = available_seats - ?
                WHERE id = ?
                AND available_seats >= ?
            """, (
                current_booking["seats"],
                current_booking["bus_id"],
                current_booking["seats"]
            ))

            if result.rowcount != 1:

                conn.rollback()
                conn.close()

                return "Sorry, requested seats are no longer available.", 409

            if payment_method == "CASH":

                payment_status = "PAY_ON_BOARD"

            else:

                # Demo payment only - no real money charged
                payment_status = "DEMO_PAID"

            conn.execute("""
                UPDATE bookings
                SET payment_method = ?,
                    payment_status = ?,
                    booking_status = 'CONFIRMED'
                WHERE id = ?
            """, (
                payment_method,
                payment_status,
                booking_id
            ))

            conn.commit()

        except sqlite3.Error:

            conn.rollback()
            conn.close()

            return "Booking failed. Please try again.", 500

        conn.close()

        return redirect(
            url_for("payment", booking_id=booking_id)
        )

    conn.close()

    return render_template(
        "payment.html",
        booking=booking
    )


# ==========================================
# BOOKING HISTORY
# ==========================================

@app.route("/my-bookings")
def my_bookings():

    conn = get_db()

    bookings = conn.execute("""
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
    """).fetchall()

    conn.close()

    return render_template(
        "my_bookings.html",
        bookings=bookings
    )


# ==========================================
# HEALTH CHECK FOR DOCKER / KUBERNETES
# ==========================================

@app.route("/health", methods=["GET"])
def health():

    return {
        "status": "healthy",
        "application": "EasyBus"
    }, 200


# ==========================================
# START APPLICATION
# ==========================================

# Initialize database when Flask/Gunicorn imports app
init_db()


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
