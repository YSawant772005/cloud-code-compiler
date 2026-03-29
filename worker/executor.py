import subprocess
import tempfile
import os
import time
import logging

logger = logging.getLogger(__name__)

# Maps language name to Docker image + filename + run command
LANGUAGE_CONFIG = {
    'python': {
        'image'  : 'python:3.12-slim',
        'filename': 'solution.py',
        'cmd'    : 'python solution.py'
    },
    'cpp': {
        'image'  : 'gcc:latest',
        'filename': 'solution.cpp',
        'cmd'    : 'g++ -o out solution.cpp && ./out'
    },
    'c': {
        'image'  : 'gcc:latest',
        'filename': 'solution.c',
        'cmd'    : 'gcc -o out solution.c && ./out'
    },
    'java': {
        'image'  : 'openjdk:21-slim',
        'filename': 'Solution.java',
        'cmd'    : 'javac Solution.java && java Solution'
    },
    'javascript': {
        'image'  : 'node:20-slim',
        'filename': 'solution.js',
        'cmd'    : 'node solution.js'
    },
    'ruby': {
        'image'  : 'ruby:3.2-slim',
        'filename': 'solution.rb',
        'cmd'    : 'ruby solution.rb'
    }
}

def execute_code(language, code, timeout=10):
    """
    Runs code inside an isolated Docker container.
    Returns dict with stdout, stderr, exit_code, execution_time.
    """
    config = LANGUAGE_CONFIG.get(language)
    if not config:
        return {
            'stdout'        : '',
            'stderr'        : f'Unsupported language: {language}',
            'exit_code'     : 1,
            'execution_time': 0.0
        }

    # Write code to a temp file on EC2
    # This file gets mounted INTO the container (read-only)
    with tempfile.TemporaryDirectory() as tmpdir:
        code_file = os.path.join(tmpdir, config['filename'])
        with open(code_file, 'w') as f:
            f.write(code)

        # Build the docker run command
        # Every flag here is a security decision
        docker_cmd = [
            'docker', 'run',
            '--rm',                          # Auto-delete container after exit
            '--network', 'none',             # NO internet access inside container
            '--memory', '128m',              # Max 128MB RAM
            '--memory-swap', '128m',         # No swap either
            '--cpus', '0.5',                 # Max half a CPU core
            '--read-only',                   # Filesystem is read-only
            '--tmpfs', '/tmp:rw,size=10m',   # Only /tmp is writable, 10MB max
            '--ulimit', 'nproc=50',          # Max 50 processes (prevents fork bombs)
            '--ulimit', 'nofile=100',        # Max 100 open files
            '-v', f'{tmpdir}:/code:ro',      # Mount code folder as read-only
            '-w', '/code',                   # Set working directory to /code
            config['image'],                 # Which language image to use
            '/bin/sh', '-c', config['cmd']   # Run the compile+execute command
        ]

        start_time = time.time()

        try:
            # Run the container — wait max `timeout` seconds
            process = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            execution_time = time.time() - start_time

            logger.info(f"Execution complete | lang={language} | "
                       f"exit={process.returncode} | time={execution_time:.3f}s")

            return {
                'stdout'        : process.stdout[:10000],  # Cap at 10KB output
                'stderr'        : process.stderr[:5000],
                'exit_code'     : process.returncode,
                'execution_time': execution_time
            }

        except subprocess.TimeoutExpired:
            # Code ran longer than timeout — kill the container
            execution_time = time.time() - start_time
            logger.warning(f"Execution timeout | lang={language} | user code exceeded {timeout}s")

            # Force kill any lingering containers
            subprocess.run(['docker', 'stop', '-t', '0',
                          '$(docker ps -q --filter ancestor=' + config['image'] + ')'],
                         shell=False, capture_output=True)

            return {
                'stdout'        : '',
                'stderr'        : f'Execution timed out after {timeout} seconds. '
                                  f'Check for infinite loops.',
                'exit_code'     : 124,
                'execution_time': execution_time
            }

        except Exception as e:
            logger.error(f"Executor error | lang={language} | error={str(e)}")
            return {
                'stdout'        : '',
                'stderr'        : f'Execution error: {str(e)}',
                'exit_code'     : 1,
                'execution_time': 0.0
            }
