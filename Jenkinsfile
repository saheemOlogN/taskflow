pipeline {
    agent { label 'docker' }
    options { disableConcurrentBuilds(); timestamps() }
    triggers { pollSCM('H/5 * * * *') }
    stages {
        stage('Checkout') { steps { checkout scm } }
        stage('Test') {
            steps {
                sh 'python3 -m venv .venv'
                sh '.venv/bin/pip install -r requirements-dev.txt'
                sh '.venv/bin/python -m pytest -q --junitxml=reports/tests.xml'
            }
        }
        stage('Deploy local demo') {
            steps { sh 'docker compose -p taskflow-demo up -d --build --wait --wait-timeout 120' }
        }
        stage('Smoke test') { steps { sh '.venv/bin/python scripts/smoke.py' } }
    }
    post {
        always { junit allowEmptyResults: true, testResults: 'reports/tests.xml' }
        failure { sh 'docker compose -p taskflow-demo logs --tail=80 || true' }
    }
}
