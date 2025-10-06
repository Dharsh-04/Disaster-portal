import pymysql
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# -----------------------------
# 1. Root MySQL connection info
# -----------------------------
ROOT_USER = "root"
ROOT_PASS = "pass"
HOST = "localhost"

# -----------------------------
# 2. App user + database details
# -----------------------------
APP_USER = "appuser"
APP_PASS = "pass"
DB_NAME = "disasterdb"

# -----------------------------
# 3. Connect as root to MySQL
# -----------------------------
conn = pymysql.connect(
    host=HOST,
    user=ROOT_USER,
    password=ROOT_PASS,
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=True
)

try:
    with conn.cursor() as cursor:
        # Create database if not exists
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        print(f"✅ Database '{DB_NAME}' created or already exists.")

        # Create app user
        cursor.execute(f"CREATE USER IF NOT EXISTS '{APP_USER}'@'localhost' IDENTIFIED BY '{APP_PASS}';")
        print(f"✅ User '{APP_USER}' created or already exists.")

        # Grant privileges
        cursor.execute(f"GRANT ALL PRIVILEGES ON {DB_NAME}.* TO '{APP_USER}'@'localhost';")
        cursor.execute("FLUSH PRIVILEGES;")
        print(f"✅ Granted all privileges on '{DB_NAME}' to '{APP_USER}'.")
finally:
    conn.close()

# -----------------------------
# 4. Define SQLAlchemy models
# -----------------------------
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{APP_USER}:{APP_PASS}@{HOST}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Volunteer(db.Model):
    __tablename__ = 'volunteer'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    skills = db.Column(db.String(200))
    location = db.Column(db.String(100))
    availability = db.Column(db.String(50))
    status = db.Column(db.String(20), default='available')

class NGO(db.Model):
    __tablename__ = 'ngo'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(15))

class Request(db.Model):
    __tablename__ = 'request'
    id = db.Column(db.Integer, primary_key=True)
    ngo_id = db.Column(db.Integer, db.ForeignKey('ngo.id'))
    title = db.Column(db.String(150))
    description = db.Column(db.Text)
    required_skills = db.Column(db.String(200))
    required_volunteers = db.Column(db.Integer)
    location = db.Column(db.String(100))
    status = db.Column(db.String(20), default='open')


# -----------------------------
# 5. Create tables
# -----------------------------
with app.app_context():
    db.create_all()
    print(f"✅ Tables created successfully in '{DB_NAME}' database.")
