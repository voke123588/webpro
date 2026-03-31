from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
import re
import os
import requests   # ADDED

from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app = Flask(__name__)
app.secret_key = 'webpro_secret_2026_secure'

# PostgreSQL connection (Render)
DATABASE_URL = os.environ.get("DATABASE_URL")

try:
    db = psycopg2.connect(DATABASE_URL)
    cursor = db.cursor()
except:
    db = None
    cursor = None

# Escort data
escorts = [
    {
        'name': 'Tatiana',
        'img': 'tatiana.jpg',
        'photos': ['tatiana1.jpg', 'tatiana2.jpg'],
        'videos': ['tatiana.mp4'],
        'phone': '0712345678',
        'gender': 'Female',
        'orientation': 'Straight',
        'age': 25,
        'nationality': 'Kenyan',
        'county': 'Nairobi',
        'city': 'Westlands',
        'services': 'Massage, Companionship, Escort',
        'description': 'I am passionate, discreet, and love a good conversation.',
        'more': 'Available any day, any time. Respect and hygiene is a must.'
    },
    {
        'name': 'Bella',
        'img': 'bella.jpg',
        'photos': [],
        'videos': [],
        'phone': '0798765432',
        'gender': 'Female',
        'orientation': 'Bisexual',
        'age': 23,
        'nationality': 'Ugandan',
        'county': 'Mombasa',
        'city': 'Nyali',
        'services': 'Escort, Overnight Stay',
        'description': 'Fun, friendly, and adventurous.',
        'more': 'Best for weekend getaways. Fluent in English and Swahili.'
    }
]

@app.route('/')
def welcome():
    girls_preview = [
        {key: girl[key] for key in ['name', 'img', 'photos', 'videos', 'phone']}
        for girl in escorts
    ]
    username = session.get('username')
    return render_template('welcome.html', girls=girls_preview, username=username)


# MODIFIED: Now loads profiles from database
@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))

    cursor.execute("SELECT * FROM profiles")
    girls = cursor.fetchall()

    return render_template('profile.html', girls=girls, username=session.get('username'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if db is None:
            flash("Database connection error.")
            return redirect(url_for('login'))

        action = request.form.get('action')
        email = request.form['email']
        password = request.form['password']
        cursor_local = db.cursor()

        if action == 'signup':
            username = request.form.get('username')
            confirm_password = request.form.get('confirm_password')

            if not re.match("^[a-zA-Z0-9]+$", username):
                flash('Username must contain only letters and numbers.')
                return redirect(url_for('login'))

            if password != confirm_password:
                flash('Passwords do not match.')
                return redirect(url_for('login'))

            cursor_local.execute("SELECT * FROM users WHERE email = %s", (email,))
            if cursor_local.fetchone():
                flash('Email already registered.')
                return redirect(url_for('login'))

            cursor_local.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                (username, email, password)
            )
            db.commit()
            flash('Signup successful. Please sign in.')
            return redirect(url_for('login'))

        elif action == 'signin':
            cursor_local.execute(
                "SELECT * FROM users WHERE email = %s AND password = %s",
                (email, password)
            )
            user = cursor_local.fetchone()
            if user:
                session['user'] = email
                session['username'] = user[1]
                return redirect(url_for('profile'))
            else:
                flash('Invalid credentials.')
                return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        if db is None:
            flash("Database connection error.")
            return redirect(url_for('forgot_password'))

        email = request.form['email']
        cursor_local = db.cursor()
        cursor_local.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor_local.fetchone()
        if user:
            return redirect(url_for('reset_password', email=email))
        else:
            flash('Email not found.')
            return redirect(url_for('forgot_password'))
    return render_template('forgot_password.html')


@app.route('/reset-password/<email>', methods=['GET', 'POST'])
def reset_password(email):
    if request.method == 'POST':
        if db is None:
            flash("Database connection error.")
            return redirect(url_for('login'))

        new_password = request.form['new_password']
        cursor_local = db.cursor()
        cursor_local.execute("UPDATE users SET password = %s WHERE email = %s", (new_password, email))
        db.commit()
        flash('Password updated. You can now log in.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', email=email)

@app.route('/payment')
def payment():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('payment.html')

@app.route('/verify')
def verify():
    if 'user' not in session:
        return redirect(url_for('login'))

    plan = request.args.get('plan')

    prices = {
        'basic': 200,
        'standard': 500,
        'premium': 1000
    }

    if plan not in prices:
        flash("Please select a payment plan.")
        return redirect(url_for('payment'))

    amount = prices[plan]

    return render_template('verify.html', plan=plan, amount=amount)


# NEW: PAYHERO STK PUSH
@app.route('/stk_push', methods=['POST'])
def stk_push():
    if 'user' not in session:
        return redirect(url_for('login'))

    phone = request.form.get('phone')
    amount = request.form.get('amount')
    plan = request.form.get('plan')
    user_email = session['user']

    url = "https://backend.payhero.co.ke/api/v2/payments"

    headers = {
        "Authorization": "Basic " + os.environ.get("PAYHERO_AUTH"),
        "Content-Type": "application/json"
    }

    payload = {
        "amount": amount,
        "phone_number": phone,
        "account_number": plan,
        "channel_id": os.environ.get("PAYHERO_ACCOUNT"),
        "provider": "m-pesa"
    }

    requests.post(url, json=payload, headers=headers)

    cursor.execute("""
        INSERT INTO payments (user_email, phone, plan, method, status)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_email, phone, plan, 'mpesa', 'pending'))

    db.commit()

    flash("STK Push sent to your phone.")
    return redirect(url_for('profile'))


# NEW: PAYHERO CALLBACK
@app.route('/payhero_callback', methods=['POST'])
def payhero_callback():
    data = request.json
    print(data)

    try:
        phone = data.get("phone_number")
        status = data.get("status")

        if status == "SUCCESS":
            cursor.execute("""
                UPDATE payments
                SET status = 'verified'
                WHERE phone = %s AND status = 'pending'
            """, (phone,))
            db.commit()
    except Exception as e:
        print(e)

    return {"status": "received"}


# NEW: ADMIN LOGIN
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == "admin" and password == "admin123":
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid admin login")

    return render_template('admin_login.html')


# NEW: ADMIN DASHBOARD
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin'))

    cursor.execute("SELECT * FROM profiles")
    profiles = cursor.fetchall()

    return render_template('admin_dashboard.html', profiles=profiles)


# NEW: ADD PROFILE
@app.route('/admin/add_profile', methods=['POST'])
def add_profile():
    if 'admin' not in session:
        return redirect(url_for('admin'))

    name = request.form.get('name')
    age = request.form.get('age')
    city = request.form.get('city')
    services = request.form.get('services')
    description = request.form.get('description')
    phone = request.form.get('phone')

    image_file = request.files['image']
    filename = secure_filename(image_file.filename)
    image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    cursor.execute("""
        INSERT INTO profiles (name, age, city, services, description, phone, image)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (name, age, city, services, description, phone, filename))

    db.commit()
    return redirect(url_for('admin_dashboard'))


# NEW: SEARCH
@app.route('/search')
def search():
    city = request.args.get('city')

    cursor.execute("SELECT * FROM profiles WHERE city ILIKE %s", ('%' + city + '%',))
    results = cursor.fetchall()

    return render_template('profile.html', girls=results)


@app.route('/verify_payment', methods=['POST'])
def verify_payment():
    if 'user' not in session:
        return redirect(url_for('login'))

    method = request.form.get('method')
    plan = request.form.get('package')
    user_email = session['user']

    prices = {'basic': 200, 'standard': 500, 'premium': 1000}
    expected_amount = prices.get(plan)

    if method == 'mpesa':
        mpesa_message = request.form.get('mpesa_message')
        match = re.search(r'Ksh\s?(\d+(?:\.\d{1,2})?)', mpesa_message)

        if match:
            try:
                amount_sent = float(match.group(1))
                if amount_sent == expected_amount:
                    cursor.execute("""
                        INSERT INTO payments (user_email, phone, plan, method, status)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (user_email, 'mpesa message', plan, 'mpesa', 'verified'))
                    db.commit()
                    return redirect('https://www.nairobihot.com/')
                else:
                    flash(f"Ksh {amount_sent} sent does not match expected {expected_amount}.")
            except ValueError:
                flash("Error reading amount from message.")
        else:
            flash("Invalid M-PESA message. Could not extract amount.")
        return redirect(url_for('verify'))

    flash("Card payments are not supported.")
    return redirect(url_for('verify'))


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('welcome'))


# UPDATED: CREATE TABLES (added profiles table)
@app.route('/create_tables')
def create_tables():
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50),
                email VARCHAR(100),
                password VARCHAR(100)
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                user_email VARCHAR(100),
                phone VARCHAR(20),
                plan VARCHAR(20),
                method VARCHAR(20),
                status VARCHAR(20)
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                age INT,
                city VARCHAR(100),
                services VARCHAR(200),
                description TEXT,
                phone VARCHAR(20),
                image VARCHAR(200)
            );
        """)

        db.commit()
        return "Tables created successfully!"

    except Exception as e:
        db.rollback()   # IMPORTANT FIX
        return str(e)

# Important for Render
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))