pipeline {
    agent { label 'windows' }
    options { disableConcurrentBuilds() }
    triggers { pollSCM('H/5 * * * *') }
    stages {
        stage('Checkout') { steps { checkout scm } }
        stage('Install') {
            steps {
                bat 'if not exist .venv\\Scripts\\python.exe python -m venv .venv'
                bat '.venv\\Scripts\\python.exe -m pip install -r requirements-dev.txt'
            }
        }
        stage('Test') { steps { bat '.venv\\Scripts\\python.exe -m pytest -q --junitxml=reports/tests.xml' } }
        stage('Build') {
            steps {
                bat '.venv\\Scripts\\python.exe scripts/native.py build'
                archiveArtifacts artifacts: 'dist/taskflow.zip', fingerprint: true
            }
        }
        stage('Prepare native tools') { steps { bat '.venv\\Scripts\\python.exe scripts/native.py setup' } }
        stage('Deploy and monitor') {
            steps {
                withEnv(['JENKINS_NODE_COOKIE=taskflow-demo-service']) {
                    bat '.venv\\Scripts\\python.exe scripts/native.py deploy'
                }
            }
        }
    }
    post { always { junit allowEmptyResults: true, testResults: 'reports/tests.xml' } }
}
