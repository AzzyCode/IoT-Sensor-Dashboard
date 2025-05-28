import os
from dotenv import load_dotenv
import logging
from flask import Flask, render_template, jsonify, redirect, url_for, request
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import socket

load_dotenv()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s -%(levelname)s - %(message)s' )
logger = logging.getLogger(__name__)

# --- Load sensitive info from environment variables ---
DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME")
SECRET_KEY = os.environ.get("SECRET_KEY")

def get_db_connection():
    try:
        conn = pymysql.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except pymysql.MySQLError as e:
        logger.error(f"Database connection error: {e}")
        return None

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'

# User model for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database when loading user")
        return None
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, password FROM users WHERE id = %s", (user_id,))
            user_data = cursor.fetchone()
        if user_data:
            return User(user_data['id'], user_data['name'], user_data['password'])
        return None
    except Exception as e:
        logger.error(f"Error loading user: {e}")
        return None
    finally:
        conn.close()

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            return render_template('login.html', error='Username and password are required')
        db_conn = get_db_connection()
        if not db_conn:
            logger.error("Database connection failed during login.")
            return render_template('login.html', error="Database connection error. Please try again later.")
        try:
            with db_conn.cursor() as cursor:
                cursor.execute("SELECT id, name, password FROM users WHERE name = %s", (username,))
                user_data = cursor.fetchone()
            if user_data and check_password_hash(user_data['password'], password):
                user = User(user_data['id'], user_data['name'], user_data['password'])
                login_user(user)
                logger.info(f"User {username} logged in successfully.")
                return redirect(url_for('index'))
            else:
                logger.warning(f"Failed login attempt for username: {username}")
                return render_template('login.html', error="Invalid username or password")
        except Exception as e:
            logger.error(f"SQL error during login: {e}")
            return render_template('login.html', error="An error occurred. Please try again later.")
        finally:
            db_conn.close()
    else:
        return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login_page'))

@app.route('/index')
@login_required
def index():
    db_conn = get_db_connection()
    if not db_conn:
        logger.error("Database connection failed when accessing index page.")
        return render_template("error.html", error="Database connection error")
    try:
        with db_conn.cursor() as cursor:
            cursor.execute("SELECT datetime, temperature, humidity FROM sensor_data ORDER BY id DESC LIMIT 10")
            data = cursor.fetchall()
        return render_template("index.html", sensor_data=data or [])
    except Exception as e:
        logger.error(f"SQL error on index page: {e}")
        return render_template("error.html", error="Failed to retrieve sensor data")
    finally:
        db_conn.close()

@app.route('/signup', methods=['GET', 'POST'])
def signup_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        if not username or not password or not email:
            return render_template('signup.html', error="Username, password, and email are required")
        password_hash = generate_password_hash(password)
        db_conn = get_db_connection()
        if not db_conn:
            logger.error("Database connection failed during signup")
            return render_template('signup.html', error="Database connection error")
        try:
            with db_conn.cursor() as cursor:
                # Check if username already exists
                cursor.execute("SELECT id FROM users WHERE name = %s", (username,))
                if cursor.fetchone():
                    return render_template('signup.html', error="Username already exists")
                # Insert new user
                cursor.execute("INSERT INTO users (name, password, email) VALUES (%s, %s, %s)", 
                              (username, password_hash, email))
            db_conn.commit()
            logger.info(f"New user registered: {username}")
            return redirect(url_for('login_page'))
        except Exception as e:
            logger.error(f"Error during user registration: {e}")
            return render_template('signup.html', error="Registration failed. Please try again.")
        finally:
            db_conn.close()
    return render_template('signup.html')    

@app.route('/signupbis')
def signup_page_bis():
    return render_template('signupbis.html')

@app.route("/sensor-data")
@login_required
def sensor_data():
    db_conn = get_db_connection()
    if not db_conn:
        logger.error("Database connection failed when retrieving sensor data")
        return jsonify({"error": "Database connection error"}), 500
    try:
        with db_conn.cursor() as cursor:
            cursor.execute("SELECT datetime, temperature, humidity FROM sensor_data ORDER BY id DESC LIMIT 100")
            sensor_data = cursor.fetchall()
        if not sensor_data:
            logger.warning("No sensor data found for /sensor-data endpoint.")
        return jsonify(sensor_data)
    except Exception as e:
        logger.error(f"SQL error on /sensor-data endpoint: {e}")
        return jsonify({"error": "Failed to retrieve sensor data"}), 500
    finally:
        db_conn.close()

@app.route('/check-db')
def check_db():
    db_conn = get_db_connection()
    if not db_conn:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500
    try:
        with db_conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        return jsonify({"status": "ok", "result": result})
    except Exception as e:
        logger.error(f"Error checking DB: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db_conn.close()

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error="404 - Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', error="500 - Internal server error"), 500

if __name__ == "__main__":
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    logger.info(f"Server is running on IP address: {local_ip}")
    if local_ip.startswith("127."):
        local_ip = os.popen("hostname -I").read().strip().split()[0]
    logger.info(f"Server is accessible on network IP address: {local_ip}")
    app.run(host=local_ip , port=5001, debug=True, ssl_context=("cert.pem", "key.pem"))
