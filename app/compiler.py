from flask import Blueprint, request, jsonify
from app.models import db, Submission, Result
import redis
import json
import jwt
import os
import logging
from functools import wraps
from datetime import datetime
SECRET_KEY = "my_super_secret_key_12345678901234567890"
compiler_bp = Blueprint('compiler', __name__)
logger      = logging.getLogger(__name__)

# Connect to ElastiCache Redis
redis_client = redis.Redis.from_url(
    os.getenv('REDIS_URL'),
    decode_responses=True
)

SUPPORTED_LANGUAGES = ['python', 'cpp', 'java', 'javascript', 'ruby', 'c']

# ── JWT Auth Decorator ─────────────────────────────────
# This protects routes — user must send valid JWT token
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({"error": "Missing token"}), 401

        try:
            # Extract token properly
            parts = auth_header.split(" ")
            if len(parts) != 2:
                return jsonify({"error": "Invalid token format"}), 401

            token = parts[1]

            # Decode token
            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

            request.user_id = decoded["user_id"]

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401

        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        except Exception as e:
            return jsonify({"error": str(e)}), 401

        return f(*args, **kwargs)

    return decorated

# ── SUBMIT CODE ───────────────────────────────────────
@compiler_bp.route('/compile', methods=['POST'])
def compile_code():
    from flask import request, jsonify
    import subprocess
    import tempfile

    data = request.get_json()

    code = data.get("code")

    try:
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
            f.write(code.encode())
            file_path = f.name

        # Run Python code
        result = subprocess.run(
            ["python3", file_path],
            capture_output=True,
            text=True,
            timeout=5
        )

        return jsonify({
            "stdout": result.stdout,
            "stderr": result.stderr,
            "status": "success"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
# ── GET RESULT ────────────────────────────────────────
@compiler_bp.route('/result/<job_id>', methods=['GET'])
def get_result(job_id):
    submission = Submission.query.filter_by(
        job_id  = job_id,
        user_id = 1
    ).first()

    if not submission:
        return jsonify({'error': 'Job not found'}), 404

    if submission.status == 'pending':
        return jsonify({'status': 'pending', 'message': 'Still in queue...'}), 202

    if submission.status == 'running':
        return jsonify({'status': 'running', 'message': 'Currently executing...'}), 202

    # Job completed — return result from RDS
    result = submission.result
    if not result:
        return jsonify({'status': 'error', 'message': 'Result not found'}), 404

    return jsonify({
        'status'         : submission.status,
        'language'       : submission.language,
        'stdout'         : result.stdout,
        'stderr'         : result.stderr,
        'exit_code'      : result.exit_code,
        'execution_time' : f"{result.execution_time:.3f}s"
    }), 200


# ── GET HISTORY ───────────────────────────────────────
@compiler_bp.route('/history', methods=['GET'])
@token_required
def get_history():
    submissions = Submission.query.filter_by(
        user_id=request.user_id
    ).order_by(Submission.created_at.desc()).limit(20).all()

    history = []
    for s in submissions:
        history.append({
            'job_id'     : s.job_id,
            'language'   : s.language,
            'status'     : s.status,
            'created_at' : s.created_at.isoformat(),
            'code_preview': s.code[:100] + '...' if len(s.code) > 100 else s.code
        })

    return jsonify({'history': history}), 200
