
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

DB = Path(__file__).with_name("bus_booking.db")


def connect():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS buses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operator TEXT,
                source TEXT,
                destination TEXT,
                travel_date TEXT,
                departure TEXT,
                arrival TEXT,
                price REAL,
                total_seats INTEGER
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                passenger_name TEXT,
                email TEXT,
                bus_id INTEGER,
                seat_count INTEGER,
                total_amount REAL,
                booked_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        count = db.execute(
            "SELECT COUNT(*) FROM buses"
        ).fetchone()[0]

        if count == 0:
            buses = [
                ("Orange Travels", "Hyderabad", "Vijayawada",
                 "2026-12-01", "22:00", "05:00", 650, 40),

                ("VRL Travels", "Hyderabad", "Bengaluru",
                 "2026-12-01", "21:30", "07:30", 950, 36),

                ("Kaveri Travels", "Vijayawada", "Hyderabad",
                 "2026-12-02", "21:00", "04:30", 600, 40),

                ("SRS Travels", "Bengaluru", "Hyderabad",
                 "2026-12-02", "20:00", "06:00", 900, 36)
            ]

            db.executemany("""
                INSERT INTO buses
                (operator, source, destination, travel_date,
                 departure, arrival, price, total_seats)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, buses)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search")
def search():

    source = request.args.get("source", "").strip()
    destination = request.args.get("destination", "").strip()
    date = request.args.get("travel_date", "").strip()

    if not source or not destination or not date:
        flash("Please enter all journey details.")
        return redirect(url_for("index"))

    with connect() as db:
        buses = db.execute("""
            SELECT b.*,
            b.total_seats - COALESCE(
                (SELECT SUM(seat_count)
                 FROM bookings
                 WHERE bus_id = b.id), 0
            ) AS available_seats
            FROM buses b
            WHERE lower(source) = lower(?)
            AND lower(destination) = lower(?)
            AND travel_date = ?
        """, (source, destination, date)).fetchall()

    return render_template(
        "search.html",
        buses=buses,
        source=source,
        destination=destination,
        date=date
    )


@app.route("/book/<int:bus_id>", methods=["GET", "POST"])
def book(bus_id):

    with connect() as db:

        bus = db.execute("""
            SELECT b.*,
            b.total_seats - COALESCE(
                (SELECT SUM(seat_count)
                 FROM bookings
                 WHERE bus_id = b.id), 0
            ) AS available_seats
            FROM buses b
            WHERE b.id = ?
        """, (bus_id,)).fetchone()

        if bus is None:
            flash("Bus not found.")
            return redirect(url_for("index"))

        if request.method == "POST":

            name = request.form.get("passenger_name", "").strip()
            email = request.form.get("email", "").strip()

            try:
                seats = int(request.form.get("seat_count", "0"))
            except ValueError:
                seats = 0

            if not name or not email or seats < 1:
                flash("Enter valid passenger details.")

            elif seats > bus["available_seats"]:
                flash("Not enough seats available.")

            else:
                total = seats * bus["price"]

                cursor = db.execute("""
                    INSERT INTO bookings
                    (passenger_name, email, bus_id,
                     seat_count, total_amount)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, email, bus_id, seats, total))

                db.commit()

                return redirect(
                    url_for(
                        "confirmation",
                        booking_id=cursor.lastrowid
                    )
                )

    return render_template("book.html", bus=bus)


@app.route("/confirmation/<int:booking_id>")
def confirmation(booking_id):

    with connect() as db:
        booking = db.execute("""
            SELECT bk.*, b.operator, b.source, b.destination,
                   b.travel_date, b.departure, b.arrival
            FROM bookings bk
            JOIN buses b ON b.id = bk.bus_id
            WHERE bk.id = ?
        """, (booking_id,)).fetchone()

    if booking is None:
        flash("Booking not found.")
        return redirect(url_for("index"))

    return render_template(
        "confirmation.html",
        booking=booking
    )


@app.route("/bookings")
def bookings():

    with connect() as db:
        rows = db.execute("""
            SELECT bk.*, b.source, b.destination, b.travel_date
            FROM bookings bk
            JOIN buses b ON b.id = bk.bus_id
            ORDER BY bk.booked_at DESC
        """).fetchall()

    return render_template("bookings.html", bookings=rows)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
