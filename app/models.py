from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80), unique=True, nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # One user can have many submissions
    submissions = db.relationship('Submission', backref='user', lazy=True)

class Submission(db.Model):
    __tablename__ = 'submissions'
    
    id         = db.Column(db.Integer, primary_key=True)
    job_id     = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    language   = db.Column(db.String(20), nullable=False)
    code       = db.Column(db.Text, nullable=False)
    status     = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # One submission has one result
    result = db.relationship('Result', backref='submission', lazy=True, uselist=False)

class Result(db.Model):
    __tablename__ = 'results'
    
    id             = db.Column(db.Integer, primary_key=True)
    submission_id  = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    stdout         = db.Column(db.Text, default='')
    stderr         = db.Column(db.Text, default='')
    exit_code      = db.Column(db.Integer, default=0)
    execution_time = db.Column(db.Float, default=0.0)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
