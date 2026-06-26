# Deployment Guide

# AI DevOps Team - Deployment Guide

**Version:** 1.0

**Date:** 2026-06-26

**Prepared by:** Charan Valaboju

---

## 1. Deployment Overview

### 1.1 Deployment Environments

| Environment | Purpose          | Infrastructure   | Scale        |
| ----------- | ---------------- | ---------------- | ------------ |
| Local       | Development      | Single machine   | 1 instance   |
| Docker      | Testing          | Docker container | 1 container  |
| Kubernetes  | Production-ready | K8s cluster      | 2-3 replicas |
| Cloud       | Enterprise       | AWS/Azure/GCP    | Auto-scaling |

### 1.2 Deployment Timeline

- **Phase 1 (V1):** Docker + local Kubernetes
- **Phase 2 (V2):** AWS ECS + RDS PostgreSQL
- **Phase 3 (V3):** Kubernetes with Prometheus/Grafana
- **Phase 4 (V4):** Multi-region deployment

---

## 2. Local Development Setup

### 2.1 Prerequisites

- Python 3.11+
- Git
- Docker (for containerization)
- Kubernetes (optional, for K8s testing)

### 2.2 Installation Steps

```bash
# 1. Clone repository
git clone https://github.com/charanvalaboju/ai-devops-team.git
cd ai-devops-team

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install .

# 4. Copy environment file
cp .env.example .env
# Edit .env and add OpenAI API key

# 5. Run application
uvicorn main:app --reload

# 6. Access API
# Visit: http://localhost:8000/docs
```

### 2.3 Environment Configuration

**File:** `.env`

```
# OpenAI Configuration
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.3

# Investigation
INVESTIGATION_TIMEOUT=20
AGENT_TIMEOUT=10

# Application
LOG_LEVEL=INFO
CORS_ORIGINS=["*"]
```

### 2.4 Running Tests

```bash
# Install test dependencies
pip install .
pip install pytest pytest-cov pytest-asyncio

# Run all tests
pytest --cov=app --cov=agents

# Run specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

---

## 3. Docker Deployment

### 3.1 Dockerfile

**File:** `docker/Dockerfile`

```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and poetry.lock if present
COPY pyproject.toml .
COPY poetry.lock .

# Create wheels
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels .

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder
COPY --from=builder /app/wheels /wheels

# Install Python dependencies
RUN pip install --no-cache /wheels/*

# Copy application code
COPY app/ ./app/
COPY agents/ ./agents/
COPY tools/ ./tools/
COPY graphs/ ./graphs/
COPY schemas/ ./schemas/

# Copy configuration
COPY .env.example ./.env

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Metadata
LABEL maintainer="Charan Valaboju"
LABEL description="AI DevOps Team - Multi-agent incident investigation"
```

### 3.2 Docker Build & Run

```bash
# Build image
docker build -f docker/Dockerfile -t ai-devops-team:latest .

# Run container
docker run -d \
  --name ai-devops \
  -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  ai-devops-team:latest

# Access logs
docker logs -f ai-devops

# Stop container
docker stop ai-devops
docker rm ai-devops
```

### 3.3 Docker Compose

**File:** `docker-compose.yml`

```yaml
version: "3.9"

services:
  api:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: ai-devops-api
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LOG_LEVEL=INFO
      - INVESTIGATION_TIMEOUT=20
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 5s
    restart: unless-stopped
    networks:
      - ai-devops-network

  # V2: Add PostgreSQL
  postgres:
    image: postgres:15-alpine
    container_name: ai-devops-db
    environment:
      POSTGRES_USER: ai_devops
      POSTGRES_PASSWORD: secure_password
      POSTGRES_DB: ai_devops_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - ai-devops-network
    restart: unless-stopped

  # V2: Add Redis
  redis:
    image: redis:7-alpine
    container_name: ai-devops-cache
    ports:
      - "6379:6379"
    networks:
      - ai-devops-network
    restart: unless-stopped

networks:
  ai-devops-network:
    driver: bridge

volumes:
  postgres_data:
```

**Run:**

```bash
docker-compose up -d
docker-compose logs -f api
docker-compose down
```

---

## 4. Kubernetes Deployment

### 4.1 Kubernetes Manifests

#### 4.1.1 Namespace

**File:** `k8s/namespace.yaml`

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ai-devops
  labels:
    app: ai-devops-team
```

#### 4.1.2 ConfigMap

**File:** `k8s/configmap.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ai-devops-config
  namespace: ai-devops
data:
  LOG_LEVEL: "INFO"
  INVESTIGATION_TIMEOUT: "20"
  AGENT_TIMEOUT: "10"
```

#### 4.1.3 Secret (V2)

**File:** `k8s/secret.yaml`

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: ai-devops-secrets
  namespace: ai-devops
type: Opaque
stringData:
  OPENAI_API_KEY: "sk-..."
  DATABASE_URL: "postgresql://user:pass@db:5432/ai_devops"
  REDIS_URL: "redis://redis:6379"
```

#### 4.1.4 Deployment

**File:** `k8s/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-devops-api
  namespace: ai-devops
  labels:
    app: ai-devops-team
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: ai-devops-team
  template:
    metadata:
      labels:
        app: ai-devops-team
    spec:
      containers:
        - name: api
          image: ai-devops-team:latest
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 8000
              protocol: TCP

          # Environment variables
          envFrom:
            - configMapRef:
                name: ai-devops-config
            - secretRef:
                name: ai-devops-secrets

          # Health checks
          livenessProbe:
            httpGet:
              path: /api/health
              port: http
            initialDelaySeconds: 10
            periodSeconds: 10
            timeoutSeconds: 3
            failureThreshold: 3

          readinessProbe:
            httpGet:
              path: /api/health
              port: http
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 2
            failureThreshold: 2

          # Resource limits
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"

          # Security
          securityContext:
            runAsNonRoot: true
            runAsUser: 1000
            readOnlyRootFilesystem: true
            allowPrivilegeEscalation: false

          # Volumes
          volumeMounts:
            - name: tmp
              mountPath: /tmp

      volumes:
        - name: tmp
          emptyDir: {}

      # Pod disruption budget
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchExpressions:
                    - key: app
                      operator: In
                      values:
                        - ai-devops-team
                topologyKey: kubernetes.io/hostname
```

#### 4.1.5 Service

**File:** `k8s/service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: ai-devops-service
  namespace: ai-devops
  labels:
    app: ai-devops-team
spec:
  type: LoadBalancer
  selector:
    app: ai-devops-team
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: 8000
```

#### 4.1.6 Ingress

**File:** `k8s/ingress.yaml`

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-devops-ingress
  namespace: ai-devops
spec:
  ingressClassName: nginx
  rules:
    - host: ai-devops.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: ai-devops-service
                port:
                  number: 80
  tls:
    - hosts:
        - ai-devops.example.com
      secretName: ai-devops-tls
```

#### 4.1.7 HPA (Horizontal Pod Autoscaler)

**File:** `k8s/hpa.yaml`

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-devops-hpa
  namespace: ai-devops
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-devops-api
  minReplicas: 2
  maxReplicas: 5
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

### 4.2 Kubernetes Deployment Steps

```bash
# 1. Create namespace
kubectl apply -f k8s/namespace.yaml

# 2. Create ConfigMap
kubectl apply -f k8s/configmap.yaml

# 3. Create Secrets (edit first!)
kubectl apply -f k8s/secret.yaml

# 4. Deploy application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# 5. Check deployment status
kubectl get pods -n ai-devops
kubectl describe pod <pod-name> -n ai-devops

# 6. Check logs
kubectl logs -n ai-devops -l app=ai-devops-team -f

# 7. Access service
kubectl port-forward -n ai-devops svc/ai-devops-service 8000:80
# Visit: http://localhost:8000/api/health

# 8. Scale deployment
kubectl scale deployment ai-devops-api -n ai-devops --replicas=3

# 9. Update deployment
kubectl set image deployment/ai-devops-api -n ai-devops \
  api=ai-devops-team:v2.0

# 10. Rollback
kubectl rollout undo deployment/ai-devops-api -n ai-devops
```

### 4.3 Monitoring K8s Deployment

```bash
# Get deployment status
kubectl get deployments -n ai-devops

# Watch pods
kubectl get pods -n ai-devops -w

# Check events
kubectl get events -n ai-devops

# Describe pod
kubectl describe pod <pod-name> -n ai-devops

# View resource usage
kubectl top pods -n ai-devops
```

---

## 5. AWS Deployment (V2)

### 5.1 ECS Deployment

**File:** `aws/ecs-task-definition.json`

```json
{
  "family": "ai-devops-team",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "ai-devops-team:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "LOG_LEVEL",
          "value": "INFO"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:..."
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ai-devops-team",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

---

## 6. CI/CD Pipeline

### 6.1 GitHub Actions Workflow

**File:** `.github/workflows/deploy.yml`

```yaml
name: Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install .
        pip install pytest
      run: pytest --cov=app --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v3

    - name: Build Docker image
      run: docker build -t ai-devops-team:${{ github.sha }} .

    - name: Push to Docker Hub
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker tag ai-devops-team:${{ github.sha }} charanvalaboju/ai-devops-team:latest
        docker push charanvalaboju/ai-devops-team:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v3

    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/ai-devops-api \
          api=ai-devops-team:${{ github.sha }} \
          -n ai-devops
        kubectl rollout status deployment/ai-devops-api -n ai-devops
      env:
        KUBECONFIG: ${{ secrets.KUBECONFIG }}
```

---

## 7. Monitoring & Logging

### 7.1 Prometheus Metrics (V2)

**File:** `k8s/prometheus-config.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: ai-devops
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s

    scrape_configs:
    - job_name: 'ai-devops'
      static_configs:
      - targets: ['localhost:8000']
      metrics_path: '/metrics'
```

### 7.2 Logging with ELK Stack (V2)

```yaml
# Add to docker-compose.yml
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
  environment:
    - discovery.type=single-node
  ports:
    - "9200:9200"

kibana:
  image: docker.elastic.co/kibana/kibana:8.0.0
  ports:
    - "5601:5601"

filebeat:
  image: docker.elastic.co/beats/filebeat:8.0.0
  volumes:
    - ./filebeat.yml:/usr/share/filebeat/filebeat.yml
```

---

## 8. Backup & Disaster Recovery

### 8.1 Database Backup (V2)

```bash
# PostgreSQL backup
pg_dump -U ai_devops ai_devops_db > backup.sql

# Restore
psql -U ai_devops ai_devops_db < backup.sql

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U ai_devops ai_devops_db | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

---

## 9. Security Hardening

### 9.1 Network Security

- Enable network policies in Kubernetes
- Use TLS for all communications
- API rate limiting
- DDoS protection (CloudFlare/AWS Shield)

### 9.2 Container Security

- Use non-root user (already configured)
- Read-only root filesystem
- Security scanning with Trivy
- Image signing

### 9.3 Secrets Management

- Use AWS Secrets Manager / Azure KeyVault
- Never commit secrets
- Rotate credentials regularly
- Audit secret access

---

## 10. Troubleshooting

### 10.1 Common Issues

**Pod won't start:**

```bash
kubectl describe pod <name> -n ai-devops
kubectl logs <name> -n ai-devops
```

**High memory usage:**

```bash
kubectl top pods -n ai-devops
# Increase resource limits if needed
```

**API is slow:**

```bash
# Check database queries (V2)
# Check external API calls
# Monitor with prometheus
```

---

## 11. Rollback Procedures

### 11.1 Kubernetes Rollback

```bash
# View rollout history
kubectl rollout history deployment/ai-devops-api -n ai-devops

# Rollback to previous version
kubectl rollout undo deployment/ai-devops-api -n ai-devops

# Rollback to specific revision
kubectl rollout undo deployment/ai-devops-api -n ai-devops --to-revision=2
```

---

## 12. Version History

| Version | Date       | Changes                  |
| ------- | ---------- | ------------------------ |
| 1.0     | 2026-06-26 | Initial deployment guide |

---

**Document Version:** 1.0  
**Last Updated:** 2026-06-26  
**Status:** Approved
