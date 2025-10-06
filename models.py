from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

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
    __tablename__ = 'ngo'   # ✅ Explicitly set table name
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(15))


class Request(db.Model):
    __tablename__ = 'request'
    id = db.Column(db.Integer, primary_key=True)
    ngo_id = db.Column(db.Integer, db.ForeignKey('ngo.id'))  # ✅ Fixed reference
    title = db.Column(db.String(150))
    description = db.Column(db.Text)
    required_skills = db.Column(db.String(200))
    required_volunteers = db.Column(db.Integer)
    location = db.Column(db.String(100))
    status = db.Column(db.String(20), default='open')

