"""Exercise the deployed API, then remove only the task this check creates."""
import json
import os
from urllib.request import Request, urlopen

base = os.getenv('API_URL', 'http://127.0.0.1:5000')


def call(path, method='GET', data=None):
    body = json.dumps(data).encode() if data is not None else None
    with urlopen(Request(base + path, data=body, method=method,
                         headers={'Content-Type': 'application/json'}), timeout=10) as response:
        raw = response.read()
        return json.loads(raw) if raw else None


assert call('/health')['status'] == 'ok'
task = call('/tasks', 'POST', {'title': 'Pipeline smoke test'})
try:
    assert any(item['id'] == task['id'] for item in call('/tasks'))
    assert call('/tasks/' + task['id'], 'PATCH', {'done': True})['done'] is True
finally:
    call('/tasks/' + task['id'], 'DELETE')
print('PASS: deployed API can create, read, update and delete DynamoDB tasks')
with urlopen(base + '/metrics', timeout=10) as response:
    assert 'taskflow_http_requests_total' in response.read().decode()
print('PASS: application monitoring metrics are available')
