import boto3
import pytest
from botocore.exceptions import EndpointConnectionError
from moto import mock_aws
from app import create_app


@pytest.fixture
def client():
    with mock_aws():
        db = boto3.resource('dynamodb', region_name='ap-south-1')
        table = db.create_table(TableName='test-tasks', KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
                                AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
                                BillingMode='PAY_PER_REQUEST')
        yield create_app(table).test_client()


def test_task_lifecycle(client):
    assert client.get('/health').status_code == 200
    response = client.post('/tasks', json={'title': '  Demonstrate Jenkins  '})
    assert response.status_code == 201
    task = response.json
    assert task['title'] == 'Demonstrate Jenkins'
    assert task['done'] is False
    assert client.get('/tasks').json == [task]
    path = '/tasks/' + task['id']
    assert client.patch(path, json={'done': True}).json['done'] is True
    assert client.get('/tasks').json[0]['done'] is True
    assert client.delete(path).status_code == 204
    assert client.get('/tasks').json == []


@pytest.mark.parametrize('body', [{}, {'title': ''}, {'title': ' '}, {'title': 42}, {'title': 'x' * 121}, []])
def test_invalid_title(client, body):
    assert client.post('/tasks', json=body).status_code == 400
    assert client.get('/tasks').json == []


@pytest.mark.parametrize('body', [{}, {'done': 'true'}, {'done': 1}, []])
def test_invalid_status(client, body):
    assert client.patch('/tasks/missing', json=body).status_code == 400


def test_missing_task_does_not_get_created(client):
    assert client.patch('/tasks/missing', json={'done': True}).status_code == 404
    assert client.delete('/tasks/missing').status_code == 404
    assert client.get('/tasks').json == []


def test_monitoring_records_requests_and_validation_errors(client):
    client.get('/tasks')
    client.post('/tasks', json={'title': ''})
    response = client.get('/metrics')
    assert response.status_code == 200
    metrics = response.text
    assert 'taskflow_http_requests_total{method="GET",route="/tasks",status="200"} 1.0' in metrics
    assert 'taskflow_http_requests_total{method="POST",route="/tasks",status="400"} 1.0' in metrics
    assert 'taskflow_http_request_duration_seconds_count{route="/tasks"} 2.0' in metrics


def test_database_outage_reports_unhealthy():
    class OfflineTable:
        def load(self):
            raise EndpointConnectionError(endpoint_url='http://offline:8000')

    client = create_app(OfflineTable()).test_client()
    assert client.get('/health').status_code == 503
    assert 'status="503"' in client.get('/metrics').text
