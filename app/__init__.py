from flask import Flask
from flask_migrate import Migrate
from dotenv import load_dotenv
from flask_cors import CORS
import os
import logging
import watchtower

# Load env properly
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

from app.models import db

def create_app():
    app = Flask(__name__, template_folder='../templates')

    # ✅ CORS FIX
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Config
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('JWT_SECRET')

    # DB
    db.init_app(app)
    Migrate(app, db)

    # Logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        logger.addHandler(watchtower.CloudWatchLogHandler(
            log_group='code-compiler-app',
            stream_name='flask-api'
        ))
        logger.info("CloudWatch logging initialized")
    except Exception as e:
        logger.warning(f"CloudWatch logging unavailable: {e}")

    # Routes
    from app.auth import auth_bp
    from app.compiler import compiler_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(compiler_bp)

    # Health
    @app.route('/health')
    def health():
        return {
            'status': 'healthy',
            'server': os.getenv('SERVER_NAME', 'unknown')
        }, 200

    return app
