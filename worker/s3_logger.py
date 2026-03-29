import boto3
import json
import os
import logging
from datetime import datetime

logger     = logging.getLogger(__name__)
s3_client  = boto3.client('s3', region_name=os.getenv('AWS_REGION', 'ap-south-1'))
BUCKET     = os.getenv('S3_BUCKET')

def log_execution(job_id, user_id, language, code, result):
    """
    Uploads full execution details to S3.
    Path: executions/YYYY/MM/user_id/job_id/log.json
    """
    now  = datetime.utcnow()
    key  = (f"executions/{now.year}/{now.month:02d}/"
            f"{user_id}/{job_id}/log.json")

    payload = {
        'job_id'        : job_id,
        'user_id'       : user_id,
        'language'      : language,
        'code'          : code,
        'stdout'        : result['stdout'],
        'stderr'        : result['stderr'],
        'exit_code'     : result['exit_code'],
        'execution_time': result['execution_time'],
        'timestamp'     : now.isoformat()
    }

    try:
        s3_client.put_object(
            Bucket      = BUCKET,
            Key         = key,
            Body        = json.dumps(payload),
            ContentType = 'application/json'
        )
        logger.info(f"S3 log uploaded | job_id={job_id} | key={key}")
        return key

    except Exception as e:
        # S3 logging failure should never crash the worker
        logger.error(f"S3 upload failed | job_id={job_id} | error={str(e)}")
        return None
