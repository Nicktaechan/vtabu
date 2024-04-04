from app import db

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class LearningResource(db.Model):
    __tablename__ = 'LearningResource'  # Explicitly specify the table name
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    content_type = db.Column(db.String(50))
    author = db.Column(db.String(100))
    rating = db.Column(db.Float)
    tags = db.Column(db.String(100))
    category = db.Column(db.String(100))
    url = db.Column(db.String(200))


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    educational_level = db.Column(db.String(50))
