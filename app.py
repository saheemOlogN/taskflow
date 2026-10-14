import os
import time
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from botocore.config import Config
from flask import Flask, Response, g, jsonify, request
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST


def create_app(table=None):
    app = Flask(__name__)
    registry = CollectorRegistry()
    database_up = Gauge('taskflow_database_up', 'Whether DynamoDB is reachable', registry=registry)
    requests = Counter('taskflow_http_requests_total', 'HTTP responses', ['method', 'route', 'status'], registry=registry)
    latency = Histogram('taskflow_http_request_duration_seconds', 'HTTP response time', ['route'], registry=registry)

    @app.before_request
    def start_timer():
        g.started = time.monotonic()

    @app.after_request
    def record_metrics(response):
        if request.path != '/metrics':
            route = request.url_rule.rule if request.url_rule else 'unmatched'
            requests.labels(request.method, route, str(response.status_code)).inc()
            latency.labels(route).observe(time.monotonic() - g.started)
        return response

    @app.get('/metrics')
    def metrics():
        try:
            table.load()
            database_up.set(1)
        except (BotoCoreError, ClientError):
            database_up.set(0)
        return Response(generate_latest(registry), content_type=CONTENT_TYPE_LATEST)

    if table is None:
        db = boto3.resource('dynamodb', region_name=os.getenv('AWS_DEFAULT_REGION', 'ap-south-1'),
                            config=Config(connect_timeout=2, read_timeout=2, retries={'max_attempts': 0}),
                            endpoint_url=os.getenv('DYNAMODB_ENDPOINT_URL') or None)
        table = db.Table(os.getenv('TABLE_NAME', 'devops-tasks'))

    @app.get('/health')
    def health():
        table.load()
        return jsonify(status='ok', database='reachable')

    @app.get('/tasks')
    def tasks():
        result = table.scan()
        items = result['Items']
        while 'LastEvaluatedKey' in result:
            result = table.scan(ExclusiveStartKey=result['LastEvaluatedKey'])
            items.extend(result['Items'])
        return jsonify(sorted(items, key=lambda item: item['id']))

    @app.post('/tasks')
    def add_task():
        data = request.get_json(silent=True)
        title = data.get('title') if isinstance(data, dict) else None
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 120:
            return jsonify(error='title must contain 1–120 characters'), 400
        item = {'id': str(uuid4()), 'title': title.strip(), 'done': False}
        table.put_item(Item=item)
        return jsonify(item), 201

    @app.patch('/tasks/<task_id>')
    def update_task(task_id):
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or type(data.get('done')) is not bool:
            return jsonify(error='done must be a boolean'), 400
        result = table.update_item(Key={'id': task_id}, UpdateExpression='SET done = :done',
                                  ExpressionAttributeValues={':done': data['done']},
                                  ConditionExpression='attribute_exists(id)', ReturnValues='ALL_NEW')
        return jsonify(result['Attributes'])

    @app.delete('/tasks/<task_id>')
    def delete_task(task_id):
        table.delete_item(Key={'id': task_id}, ConditionExpression='attribute_exists(id)')
        return '', 204

    @app.errorhandler(ClientError)
    def database_error(error):
        if error.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return jsonify(error='Task not found'), 404
        app.logger.exception('DynamoDB operation failed')
        return jsonify(error='Database unavailable'), 503

    @app.errorhandler(BotoCoreError)
    def database_connection_error(error):
        app.logger.exception('DynamoDB connection failed')
        return jsonify(error='Database unavailable'), 503

    return app
