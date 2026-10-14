"""Native Windows demo: setup, build, start, deploy, stop-api, stop."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.request import urlopen, urlretrieve
from zipfile import ZipFile
import psutil

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / '.runtime'
TOOLS = ROOT / '.tools'
ENV = dict(os.environ, AWS_ACCESS_KEY_ID='localdemo', AWS_SECRET_ACCESS_KEY='localdemo',
           AWS_DEFAULT_REGION='ap-south-1', DYNAMODB_ENDPOINT_URL='http://127.0.0.1:8000',
           TABLE_NAME='devops-tasks', AWS_EC2_METADATA_DISABLED='true')
ENV.pop('AWS_SESSION_TOKEN', None)


def setup():
    TOOLS.mkdir(exist_ok=True)
    db = TOOLS / 'dynamodb'
    if not (db / 'DynamoDBLocal.jar').exists():
        url = 'https://d1ni2b6xgvw0s0.cloudfront.net/v2.x/dynamodb_local_latest.zip'
        archive = TOOLS / 'dynamodb.zip'
        print('Downloading AWS DynamoDB Local...', flush=True)
        urlretrieve(url, archive)
        with urlopen(url + '.sha256', timeout=30) as response:
            expected = response.read().decode().split()[0].lower()
        if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
            raise RuntimeError('DynamoDB archive checksum mismatch')
        with ZipFile(archive) as bundle:
            bundle.extractall(db)
    prom = TOOLS / 'prometheus-3.5.0.windows-amd64'
    if not (prom / 'prometheus.exe').exists():
        base = 'https://github.com/prometheus/prometheus/releases/download/v3.5.0/'
        filename = 'prometheus-3.5.0.windows-amd64.zip'
        print('Downloading Prometheus for Windows...', flush=True)
        archive = TOOLS / filename
        urlretrieve(base + filename, archive)
        with urlopen(base + 'sha256sums.txt', timeout=30) as response:
            checksums = response.read().decode().splitlines()
        expected = next(line.split()[0] for line in checksums if line.split()[-1] == filename)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
            raise RuntimeError('Prometheus archive checksum mismatch')
        with ZipFile(archive) as bundle:
            bundle.extractall(TOOLS)
    print('Native tools ready.')


def owned(name):
    record = STATE / (name + '.json')
    if not record.exists():
        return None
    data = json.loads(record.read_text())
    try:
        proc = psutil.Process(data['pid'])
        if proc.create_time() == data['created'] and proc.exe() == data['exe']:
            return proc
    except psutil.NoSuchProcess:
        pass
    return None


def stop(name):
    proc = owned(name)
    if proc:
        # Windows virtual-environment launchers can own a Python child process.
        children = proc.children(recursive=True)
        for child in reversed(children):
            try:
                child.terminate()
            except psutil.NoSuchProcess:
                pass
        proc.terminate()
        proc.wait(timeout=15)
        _, alive = psutil.wait_procs(children, timeout=15)
        if alive:
            raise RuntimeError(f'{name} child processes did not stop')
    (STATE / (name + '.json')).unlink(missing_ok=True)


def launch(name, command, port, cwd=ROOT):
    if owned(name):
        return
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1', port)) == 0:
            raise RuntimeError(f'Port {port} is occupied by another service; stop it before continuing.')
    STATE.mkdir(exist_ok=True)
    with (STATE / (name + '.log')).open('ab') as log:
        child = subprocess.Popen(command, cwd=cwd, env=ENV, stdin=subprocess.DEVNULL,
                                 stdout=log, stderr=log,
                                 creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    proc = psutil.Process(child.pid)
    (STATE / (name + '.json')).write_text(json.dumps(
        {'pid': proc.pid, 'created': proc.create_time(), 'exe': proc.exe()}))
    for _ in range(60):
        if child.poll() is not None:
            raise RuntimeError(f'{name} exited; inspect {STATE / (name + ".log")}')
        with socket.socket() as sock:
            if sock.connect_ex(('127.0.0.1', port)) == 0:
                return
        time.sleep(1)
    raise RuntimeError(f'{name} did not start within 60 seconds; inspect its log')


def build():
    (ROOT / 'dist').mkdir(exist_ok=True)
    with ZipFile(ROOT / 'dist/taskflow.zip', 'w') as bundle:
        for filename in ['app.py', 'serve.py', 'requirements.txt']:
            bundle.write(ROOT / filename, filename)
    print('Built dist/taskflow.zip')


def start(deploy=False):
    java_home = os.getenv('JAVA_HOME')
    java = str(Path(java_home) / 'bin/java.exe') if java_home else shutil.which('java')
    if not java:
        raise RuntimeError('Install Java 17+ and set JAVA_HOME first.')
    db = TOOLS / 'dynamodb'
    if not (db / 'DynamoDBLocal.jar').exists():
        raise RuntimeError('Run scripts/native.py setup first.')
    (STATE / 'data').mkdir(parents=True, exist_ok=True)
    launch('dynamodb', [java, '-Djava.library.path=./DynamoDBLocal_lib', '-jar',
                       'DynamoDBLocal.jar', '-sharedDb', '-dbPath', str(STATE / 'data')], 8000, db)
    subprocess.run([sys.executable, str(ROOT / 'init_db.py')], env=ENV, check=True)
    release = STATE / 'release'
    if deploy or not (release / 'serve.py').exists():
        if not (ROOT / 'dist/taskflow.zip').exists():
            build()
        stop('api')
        with ZipFile(ROOT / 'dist/taskflow.zip') as bundle:
            bundle.extractall(release)
    launch('api', [sys.executable, str(release / 'serve.py')], 5000, release)
    prom = TOOLS / 'prometheus-3.5.0.windows-amd64/prometheus.exe'
    launch('prometheus', [str(prom), '--config.file=' + str(ROOT / 'monitoring/prometheus-native.yml'),
                         '--storage.tsdb.path=' + str(STATE / 'metrics'),
                         '--web.listen-address=127.0.0.1:9090'], 9090, ROOT / 'monitoring')
    subprocess.run([sys.executable, str(ROOT / 'scripts/smoke.py')], env=ENV, check=True)
    for _ in range(30):
        try:
            with urlopen('http://127.0.0.1:9090/api/v1/query?query=up', timeout=3) as response:
                result = json.load(response)['data']['result']
            if any(row['metric'].get('job') == 'taskflow' and row['value'][1] == '1' for row in result):
                print('PASS: Prometheus is scraping TaskFlow. Open http://localhost:9090/targets')
                return
        except (OSError, ValueError, KeyError):
            pass
        time.sleep(1)
    raise RuntimeError('Prometheus has not reported TaskFlow UP; inspect .runtime/prometheus.log')


if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) == 2 else ''
    if action == 'setup':
        setup()
    elif action == 'build':
        build()
    elif action in ('start', 'deploy'):
        start(deploy=action == 'deploy')
    elif action == 'stop-api':
        stop('api')
    elif action == 'stop':
        for service in ('api', 'prometheus', 'dynamodb'):
            stop(service)
    else:
        raise SystemExit('Usage: python scripts/native.py setup|build|start|deploy|stop-api|stop')
