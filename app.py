from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
import re
import os

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

@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('profile.html', girls=escorts, username=session.get('username'))

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

        db.commit()
        return "Tables created successfully!"
    except Exception as e:
        return str(e)

# Important for Render
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))