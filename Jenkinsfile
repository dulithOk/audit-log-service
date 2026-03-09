pipeline {
    agent {
        docker {
            image 'python:3.12-slim'
            args '-v /var/run/docker.sock:/var/run/docker.sock'
        }
    }

    environment {
        SERVICE_NAME    = 'audit-log-service'
        IMAGE_NAME      = "your-registry.com/${SERVICE_NAME}"
        DOCKER_REGISTRY = credentials('docker-registry-credentials')
        SONAR_TOKEN     = credentials('sonarqube-token')
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(
                        script: "git rev-parse --short HEAD",
                        returnStdout: true
                    ).trim()
                    env.IMAGE_TAG = "${env.BRANCH_NAME}-${env.GIT_COMMIT_SHORT}"
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install pytest pytest-asyncio pytest-cov ruff bandit
                '''
            }
        }

        stage('Lint') {
            steps {
                sh 'ruff check app/'
            }
        }

        stage('Security Scan') {
            steps {
                sh 'bandit -r app/ -ll -ii'
            }
        }

        stage('Test') {
            environment {
                DB_HOST     = 'localhost'
                DB_PORT     = '5432'
                DB_NAME     = 'audit_test'
                DB_USER     = 'test_user'
                DB_PASSWORD = 'test_pass'
                API_KEYS    = 'test-key'
            }
            steps {
                sh '''
                    pytest tests/ \
                        --cov=app \
                        --cov-report=xml:coverage.xml \
                        --cov-report=term-missing \
                        --cov-fail-under=80 \
                        -v
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'test-results/*.xml'
                    publishCoverage adapters: [coberturaAdapter('coverage.xml')]
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                sh """
                    docker build \
                        --target production \
                        --tag ${IMAGE_NAME}:${IMAGE_TAG} \
                        --tag ${IMAGE_NAME}:latest \
                        --label git-commit=${GIT_COMMIT_SHORT} \
                        --label build-date=\$(date -u +%Y-%m-%dT%H:%M:%SZ) \
                        .
                """
            }
        }

        stage('Push Image') {
            when {
                anyOf {
                    branch 'main'
                    branch 'release/*'
                }
            }
            steps {
                sh """
                    echo \${DOCKER_REGISTRY_PSW} | docker login your-registry.com \
                        -u \${DOCKER_REGISTRY_USR} --password-stdin
                    docker push ${IMAGE_NAME}:${IMAGE_TAG}
                    docker push ${IMAGE_NAME}:latest
                """
            }
        }

        stage('Deploy — Staging') {
            when { branch 'main' }
            steps {
                sh """
                    # Replace with your deployment mechanism (kubectl, helm, etc.)
                    echo "Deploying ${IMAGE_NAME}:${IMAGE_TAG} to staging"
                """
            }
        }

        stage('Deploy — Production') {
            when { branch 'release/*' }
            input {
                message "Promote to production?"
                ok "Deploy"
            }
            steps {
                sh """
                    echo "Deploying ${IMAGE_NAME}:${IMAGE_TAG} to production"
                """
            }
        }
    }

    post {
        success {
            echo "Pipeline succeeded — ${IMAGE_NAME}:${IMAGE_TAG}"
        }
        failure {
            mail(
                to: 'your-team@company.com',
                subject: "FAILED: ${SERVICE_NAME} pipeline on ${env.BRANCH_NAME}",
                body: "Build URL: ${env.BUILD_URL}"
            )
        }
        always {
            sh 'docker image prune -f || true'
            cleanWs()
        }
    }
}
