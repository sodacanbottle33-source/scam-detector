from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(120))

class Scan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text)
    score = db.Column(db.Integer)
    level = db.Column(db.String(50))
    user_id = db.Column(db.Integer)