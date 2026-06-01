from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
import uuid
import os
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "buspass_secret_key"

# ---------------- DATABASE INIT ----------------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        source TEXT,
        destination TEXT,
        tickets INTEGER,
        price INTEGER,
        ticket_id TEXT
    )''')

    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------
@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('book'))
    return render_template("index.html")

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user'] = username
            return redirect(url_for('book'))
        else:
            return "Invalid Credentials"

    return render_template("login.html")

# ---------------- BOOK TICKET ----------------
@app.route('/book', methods=['GET', 'POST'])
def book():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        source = request.form['source']
        destination = request.form['destination']
        tickets = int(request.form['tickets'])

        price = tickets * 50
        ticket_id = str(uuid.uuid4())[:8]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("""INSERT INTO bookings 
        (username, source, destination, tickets, price, ticket_id) 
        VALUES (?, ?, ?, ?, ?, ?)""",
        (session['user'], source, destination, tickets, price, ticket_id))

        conn.commit()
        conn.close()

        return render_template("success.html", ticket_id=ticket_id, price=price)

    return render_template("book.html")

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

# ---------------- PDF DOWNLOAD ----------------
@app.route('/download/<ticket_id>')
def download(ticket_id):

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM bookings WHERE ticket_id=?", (ticket_id,))
    data = c.fetchone()
    conn.close()

    if not data:
        return "Ticket not found"

    file_path = f"{ticket_id}.pdf"

    pdf = canvas.Canvas(file_path)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(180, 750, "BUS PASS TICKET")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(100, 700, f"Ticket ID: {data[6]}")
    pdf.drawString(100, 680, f"User: {data[1]}")
    pdf.drawString(100, 660, f"Source: {data[2]}")
    pdf.drawString(100, 640, f"Destination: {data[3]}")
    pdf.drawString(100, 620, f"Tickets: {data[4]}")
    pdf.drawString(100, 600, f"Price: ₹{data[5]}")

    pdf.save()

    return send_file(file_path, as_attachment=True)

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)