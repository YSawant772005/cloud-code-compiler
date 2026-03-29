import redis
import json
import os
import sys
import logging
import watchtower
from dotenv import load_dotenv

# Load .env before anything else
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Add parent directory to path so we can import app models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import db, Submission, Result
from app import create_app
from worker.executor import execute_code
from worker.s3_logger import log_execution

# ── Logging setup ──────────────────────────────────────
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

try:
    logger.addHandler(watchtower.CloudWatchLogHandler(
        log_group='code-compiler-workers',
        stream_name='worker-1'
    ))
except Exception:
    pass

# ── Redis connection to ElastiCache ───────────────────
redis_client = redis.Redis.from_url(
    os.getenv('REDIS_URL'),
    decode_responses=True
)

def process_job(job_data):
    """Process a single code execution job end to end."""
    job_id        = job_data['job_id']
    submission_id = job_data['submission_id']
    user_id       = job_data['user_id']
    language      = job_data['language']
    code          = job_data['code']

    logger.info(f"Processing job | job_id={job_id} | lang={language}")

    # Use Flask app context to access RDS via SQLAlchemy
    app = create_app()
    with app.app_context():

        # Update status to 'running' in RDS
        submission = Submission.query.filter_by(job_id=job_id).first()
        if not submission:
            logger.error(f"Submission not found in RDS | job_id={job_id}")
            return

        submission.status = 'running'
        db.session.commit()

        # ── Execute code in Docker container ──────────────
        result = execute_code(language, code, timeout=10)

        # ── Save result to RDS ────────────────────────────
        db_result = Result(
            submission_id  = submission_id,
            stdout         = result['stdout'],
            stderr         = result['stderr'],
            exit_code      = result['exit_code'],
            execution_time = result['execution_time']
        )
        db.session.add(db_result)

        # Update submission status based on exit code
        submission.status = 'success' if result['exit_code'] == 0 else 'error'
        db.session.commit()

        # ── Upload full log to S3 ─────────────────────────
        log_execution(job_id, user_id, language, code, result)

        logger.info(f"Job complete | job_id={job_id} | "
                   f"status={submission.status} | "
                   f"time={result['execution_time']:.3f}s")


def main():
    """
    Main worker loop.
    BRPOP blocks and waits until a job appears in Redis.
    This is more efficient than polling — worker sleeps until work arrives.
    """
    logger.info("Worker started — waiting for jobs from Redis queue...")
    logger.info(f"Connected to Redis: {os.getenv('REDIS_URL')}")

    while True:
        try:
            # BRPOP waits up to 30s for a job, then loops
            # This prevents the worker from spinning and wasting CPU
            job = redis_client.brpop('code_execution_queue', timeout=30)

            if job is None:
                # No job in 30 seconds — just log and keep waiting
                logger.info("Queue empty — waiting...")
                continue

            # job = ('code_execution_queue', '{json data}')
            _, job_json = job
            job_data    = json.loads(job_json)

            process_job(job_data)

        except redis.ConnectionError as e:
            logger.error(f"Redis connection lost: {e} — retrying in 5s")
            import time; time.sleep(5)

        except Exception as e:
            logger.error(f"Worker error: {e}")
            import time; time.sleep(2)


if __name__ == '__main__':
    main()
