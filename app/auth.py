from flask import Blueprint, request, jsonify
from app.models import db, User
import bcrypt
import jwt
import os
import logging
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

SECRET_KEY = "my_super_secret_key_12345678901234567890"  # change later

# ── REGISTER ──────────────────────────────────────────
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Validate input
    if not all(k in data for k in ['username', 'email', 'password']):
        return jsonify({'error': 'Missing required fields'}), 400

    # Check if user exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409

    try:
        # Hash password
        hashed = bcrypt.hashpw(
            data['password'].encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        # Create user
        user = User(
            username=data['username'],
            email=data['email'],
            password=hashed
        )

        db.session.add(user)
        db.session.commit()

        return jsonify({'message': 'User registered successfully'}), 201

    except Exception as e:
        logger.error(f"Register error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


# ── LOGIN ──────────────────────────────────────────
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    if not all(k in data for k in ['email', 'password']):
        return jsonify({'error': 'Missing fields'}), 400

    try:
        user = User.query.filter_by(email=data['email']).first()

        # 🔥 FIX IS HERE
        if user and bcrypt.checkpw(
            data['password'].encode('utf-8'),
            user.password.encode('utf-8')
        ):
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, SECRET_KEY, algorithm='HS256')

            return jsonify({
                'message': 'Login successful',
                'token': token
            }), 200

        return jsonify({'error': 'Invalid credentials'}), 401

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
