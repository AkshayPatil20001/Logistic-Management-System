from flask import Flask, render_template, request, redirect, session, flash, url_for
import sqlite3, base64
from werkzeug.security import generate_password_hash, check_password_hash
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session
import base64
import sqlite3
import io


app = Flask(__name__)
app.secret_key = 'replace_this_with_a_strong_secret'
DB_PATH = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ✅ Add this custom Jinja2 filter for base64 encoding
@app.template_filter('b64encode')
def b64encode_filter(data):
    if data is None:
        return ''
    return base64.b64encode(data).decode('utf-8')

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name').strip()
        username = request.form.get('username').strip()
        email = request.form.get('email').strip()
        mobile = request.form.get('mobile').strip()
        business_name = request.form.get('business_name').strip()
        password = request.form.get('password')
        role = request.form.get('role')

        profile_file = request.files.get('profile_image')
        company_file = request.files.get('company_image')

        profile_blob = profile_file.read() if profile_file else None
        company_blob = company_file.read() if company_file else None

        if not (name and username and password and role):
            flash('Please fill required fields', 'error')
            return redirect(url_for('signup'))

        pw_hash = generate_password_hash(password)

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('''INSERT INTO users 
                (name, username, email, mobile, business_name, password, role, profile_image, company_image)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (name, username, email, mobile, business_name, pw_hash, role, profile_blob, company_blob))
            conn.commit()
            flash('Account created. Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists.', 'error')
            return redirect(url_for('signup'))
        finally:
            conn.close()

    return render_template('signup.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['name'] = user['name']
            flash(f'Welcome, {user["name"]}!', 'success')
            if user['role'] == 'developer':
                return redirect(url_for('developer_dashboard'))
            else:
                return redirect(url_for('owner_dashboard'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'info')
    return redirect(url_for('index'))

# Owner Dashboard
@app.route('/owner_dashboard')
def owner_dashboard():
    if 'user_id' not in session or session.get('role') != 'owner':
        flash('Please login as Business Owner', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    trucks = conn.execute('SELECT * FROM trucks WHERE owner_id = ? ORDER BY created_at DESC', (session['user_id'],)).fetchall()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()

    profile_image = base64.b64encode(user['profile_image']).decode('utf-8') if user['profile_image'] else None
    company_image = base64.b64encode(user['company_image']).decode('utf-8') if user['company_image'] else None

    return render_template('owner_dashboard.html', name=user['name'], company_name=user['business_name'],
                           current_user_image=profile_image, current_company_image=company_image, trucks=trucks)

# Add Truck
@app.route('/add_truck', methods=['POST'])
def add_truck():
    if 'user_id' not in session or session.get('role') != 'owner':
        flash('Unauthorized', 'error')
        return redirect(url_for('login'))

    truck_number = request.form.get('truck_number').strip()
    truck_model = request.form.get('truck_model').strip()
    driver_name = request.form.get('driver_name').strip()
    if not truck_number:
        flash('Truck number required', 'error')
        return redirect(url_for('owner_dashboard'))

    conn = get_db_connection()
    conn.execute('INSERT INTO trucks (owner_id, truck_number, truck_model, driver_name) VALUES (?, ?, ?, ?)',
                 (session['user_id'], truck_number, truck_model, driver_name))
    conn.commit()
    conn.close()
    flash('Truck added', 'success')
    return redirect(url_for('owner_dashboard'))

# Delete Truck
@app.route('/delete_truck/<int:truck_id>', methods=['POST'])
def delete_truck(truck_id):
    if 'user_id' not in session:
        flash('Unauthorized', 'error')
        return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM trucks WHERE id = ? AND owner_id = ?', (truck_id, session['user_id']))
    conn.commit()
    conn.close()
    flash('Truck deleted (if owned by you)', 'info')
    return redirect(url_for('owner_dashboard'))

# Update Truck
@app.route('/update_truck/<int:truck_id>', methods=['GET', 'POST'])
def update_truck(truck_id):
    if 'user_id' not in session:
        flash('Unauthorized', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    truck = conn.execute('SELECT * FROM trucks WHERE id = ? AND owner_id = ?', (truck_id, session['user_id'])).fetchone()
    if not truck:
        conn.close()
        flash('Truck not found or you are not the owner', 'error')
        return redirect(url_for('owner_dashboard'))

    if request.method == 'POST':
        truck_number = request.form.get('truck_number').strip()
        truck_model = request.form.get('truck_model').strip()
        driver_name = request.form.get('driver_name').strip()
        status = request.form.get('status').strip() or 'Active'

        conn.execute('UPDATE trucks SET truck_number=?, truck_model=?, driver_name=?, status=? WHERE id=?',
                     (truck_number, truck_model, driver_name, status, truck_id))
        conn.commit()
        conn.close()
        flash('Truck updated', 'success')
        return redirect(url_for('owner_dashboard'))

    conn.close()
    return render_template('update_truck.html', truck=truck)

# Developer Dashboard
@app.route('/developer_dashboard')
def developer_dashboard():
    if 'user_id' not in session or session.get('role') != 'developer':
        flash('Please login as Developer', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    trucks = conn.execute('SELECT * FROM trucks').fetchall()
    users_raw = conn.execute('SELECT * FROM users').fetchall()
    conn.close()

    # Convert images to base64 for display
    users = []
    for u in users_raw:
        profile_image = base64.b64encode(u['profile_image']).decode('utf-8') if u['profile_image'] else None
        company_image = base64.b64encode(u['company_image']).decode('utf-8') if u['company_image'] else None
        user_dict = dict(u)
        user_dict['profile_image'] = profile_image
        user_dict['company_image'] = company_image
        users.append(user_dict)

    return render_template('developer_dashboard.html', trucks=trucks, users=users)


if __name__ == '__main__':
    Path(DB_PATH).touch(exist_ok=True)
    app.run(debug=True)
