# Deployment Guide

This guide covers deploying the Telegram Data Collection Service in various environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Setup](#development-setup)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Production Considerations](#production-considerations)
- [Monitoring Setup](#monitoring-setup)
- [Backup and Recovery](#backup-and-recovery)

## Prerequisites

### System Requirements

- **CPU**: Minimum 2 cores, recommended 4+ cores
- **RAM**: Minimum 4GB, recommended 8GB+
- **Storage**: Minimum 20GB, recommended 100GB+ for media storage
- **Network**: Stable internet connection with proxy support

### Software Dependencies

- **Python**: 3.8 or higher
- **Docker**: 20.10+ (for containerized deployment)
- **Docker Compose**: 2.0+ (for multi-service deployment)
- **Kubernetes**: 1.20+ (for orchestrated deployment)

### External Services

- **Kafka Cluster**: For message streaming
- **Elasticsearch**: For data storage and search
- **MinIO**: For media file storage
- **Redis**: For caching and session management
- **PostgreSQL**: For metadata storage

## Development Setup

### Local Development Environment

1. **Clone the repository**
```bash
git clone <repository-url>
cd services/telegram
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Configure Telegram API credentials**
```bash
# Get API credentials from https://my.telegram.org
# Add to .env file:
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
```

6. **Start external services (using Docker Compose)**
```bash
docker-compose -f docker-compose.dev.yml up -d
```

7. **Run the service**
```bash
python main.py
```

### Development Configuration

Create a `config/dev.py` file for development-specific settings:

```python
# Development configuration
DEBUG = True
LOG_LEVEL = "DEBUG"

# Development database
DATABASE_URL = "postgresql://user:password@localhost:5432/telegram_dev"

# Development Kafka
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

# Development Elasticsearch
ELASTICSEARCH_HOSTS = ["http://localhost:9200"]

# Development MinIO
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"

# Development Redis
REDIS_HOST = "localhost"
REDIS_PORT = 6379
```

## Docker Deployment

### Single Container Deployment

1. **Build the Docker image**
```bash
docker build -t telegram-service:latest .
```

2. **Run the container**
```bash
docker run -d \
  --name telegram-service \
  -p 8000:8000 \
  -v $(pwd)/sessions:/app/sessions \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  telegram-service:latest
```

### Multi-Service Deployment with Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  telegram-service:
    build: .
    container_name: telegram-service
    ports:
      - "8000:8000"
    volumes:
      - ./sessions:/app/sessions
      - ./logs:/app/logs
      - ./config:/app/config
    environment:
      - TELEGRAM_API_ID=${TELEGRAM_API_ID}
      - TELEGRAM_API_HASH=${TELEGRAM_API_HASH}
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - ELASTICSEARCH_HOSTS=elasticsearch:9200
      - MINIO_ENDPOINT=minio:9000
      - REDIS_HOST=redis
    depends_on:
      - kafka
      - elasticsearch
      - minio
      - redis
      - postgres
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  kafka:
    image: confluentinc/cp-kafka:7.0.0
    container_name: kafka
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"

  zookeeper:
    image: confluentinc/cp-zookeeper:7.0.0
    container_name: zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  minio:
    image: minio/minio:latest
    container_name: minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data

  redis:
    image: redis:7-alpine
    container_name: redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  postgres:
    image: postgres:14-alpine
    container_name: postgres
    environment:
      POSTGRES_DB: telegram_db
      POSTGRES_USER: telegram_user
      POSTGRES_PASSWORD: telegram_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  elasticsearch_data:
  minio_data:
  redis_data:
  postgres_data:
```

3. **Deploy with Docker Compose**
```bash
docker-compose up -d
```

4. **Check service status**
```bash
docker-compose ps
docker-compose logs telegram-service
```

## Kubernetes Deployment

### Namespace Setup

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: telegram-service
```

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: telegram-service-config
  namespace: telegram-service
data:
  config.yaml: |
    kafka:
      bootstrap_servers: kafka-service:9092
      topic_prefix: telegram
    
    elasticsearch:
      hosts: ["http://elasticsearch-service:9200"]
      index_prefix: telegram
    
    minio:
      endpoint: minio-service:9000
      access_key: minioadmin
      secret_key: minioadmin
    
    redis:
      host: redis-service
      port: 6379
      db: 0
```

### Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: telegram-secrets
  namespace: telegram-service
type: Opaque
data:
  telegram-api-id: <base64-encoded-api-id>
  telegram-api-hash: <base64-encoded-api-hash>
  database-url: <base64-encoded-database-url>
```

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: telegram-service
  namespace: telegram-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: telegram-service
  template:
    metadata:
      labels:
        app: telegram-service
    spec:
      containers:
      - name: telegram-service
        image: telegram-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: TELEGRAM_API_ID
          valueFrom:
            secretKeyRef:
              name: telegram-secrets
              key: telegram-api-id
        - name: TELEGRAM_API_HASH
          valueFrom:
            secretKeyRef:
              name: telegram-secrets
              key: telegram-api-hash
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: telegram-secrets
              key: database-url
        envFrom:
        - configMapRef:
            name: telegram-service-config
        volumeMounts:
        - name: sessions
          mountPath: /app/sessions
        - name: logs
          mountPath: /app/logs
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: sessions
        persistentVolumeClaim:
          claimName: telegram-sessions-pvc
      - name: logs
        persistentVolumeClaim:
          claimName: telegram-logs-pvc
```

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: telegram-service
  namespace: telegram-service
spec:
  selector:
    app: telegram-service
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

### Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: telegram-service-ingress
  namespace: telegram-service
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: telegram-service.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: telegram-service
            port:
              number: 80
```

### Persistent Volume Claims

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: telegram-sessions-pvc
  namespace: telegram-service
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: telegram-logs-pvc
  namespace: telegram-service
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: telegram-service-hpa
  namespace: telegram-service
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: telegram-service
  minReplicas: 2
  maxReplicas: 10
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

## Production Considerations

### Security

1. **Network Security**
   - Use VPN or private networks for internal communication
   - Implement network policies in Kubernetes
   - Use TLS for all external communications

2. **Authentication & Authorization**
   - Implement proper authentication for API endpoints
   - Use service accounts in Kubernetes
   - Rotate API keys regularly

3. **Data Protection**
   - Encrypt data at rest and in transit
   - Implement proper backup strategies
   - Follow data retention policies

### Performance

1. **Resource Optimization**
   - Monitor and adjust resource limits
   - Use appropriate instance types
   - Implement caching strategies

2. **Scalability**
   - Use horizontal scaling for high load
   - Implement proper load balancing
   - Monitor and optimize database queries

3. **Monitoring**
   - Set up comprehensive monitoring
   - Implement alerting for critical issues
   - Use distributed tracing

### Reliability

1. **High Availability**
   - Deploy across multiple availability zones
   - Implement proper health checks
   - Use circuit breakers for external dependencies

2. **Disaster Recovery**
   - Regular backup of critical data
   - Test recovery procedures
   - Document incident response plans

## Monitoring Setup

### Prometheus Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    
    scrape_configs:
    - job_name: 'telegram-service'
      static_configs:
      - targets: ['telegram-service:8000']
      metrics_path: /metrics
```

### Grafana Dashboard

Create a Grafana dashboard for monitoring:

```json
{
  "dashboard": {
    "title": "Telegram Service Dashboard",
    "panels": [
      {
        "title": "Message Processing Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(telegram_messages_processed_total[5m])"
          }
        ]
      },
      {
        "title": "Active Accounts",
        "type": "stat",
        "targets": [
          {
            "expr": "telegram_active_accounts"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(telegram_errors_total[5m])"
          }
        ]
      }
    ]
  }
}
```

### Alerting Rules

```yaml
groups:
- name: telegram-service
  rules:
  - alert: HighErrorRate
    expr: rate(telegram_errors_total[5m]) > 0.1
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High error rate in Telegram service"
  
  - alert: ServiceDown
    expr: up{job="telegram-service"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Telegram service is down"
  
  - alert: HighMemoryUsage
    expr: (container_memory_usage_bytes{container="telegram-service"} / container_spec_memory_limit_bytes{container="telegram-service"}) > 0.8
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage in Telegram service"
```

## Backup and Recovery

### Data Backup Strategy

1. **Session Files**
```bash
#!/bin/bash
# Backup session files
tar -czf sessions_backup_$(date +%Y%m%d_%H%M%S).tar.gz sessions/
aws s3 cp sessions_backup_*.tar.gz s3://backup-bucket/telegram-sessions/
```

2. **Database Backup**
```bash
#!/bin/bash
# Backup PostgreSQL database
pg_dump $DATABASE_URL > db_backup_$(date +%Y%m%d_%H%M%S).sql
gzip db_backup_*.sql
aws s3 cp db_backup_*.sql.gz s3://backup-bucket/telegram-db/
```

3. **Elasticsearch Backup**
```bash
#!/bin/bash
# Create Elasticsearch snapshot
curl -X PUT "localhost:9200/_snapshot/backup_repo/snapshot_$(date +%Y%m%d_%H%M%S)?wait_for_completion=true"
```

### Recovery Procedures

1. **Service Recovery**
```bash
# Restart the service
kubectl rollout restart deployment/telegram-service -n telegram-service

# Check service status
kubectl get pods -n telegram-service
kubectl logs -f deployment/telegram-service -n telegram-service
```

2. **Data Recovery**
```bash
# Restore session files
tar -xzf sessions_backup_YYYYMMDD_HHMMSS.tar.gz

# Restore database
gunzip db_backup_YYYYMMDD_HHMMSS.sql.gz
psql $DATABASE_URL < db_backup_YYYYMMDD_HHMMSS.sql

# Restore Elasticsearch
curl -X POST "localhost:9200/_snapshot/backup_repo/snapshot_YYYYMMDD_HHMMSS/_restore"
```

### Automated Backup

Create a CronJob for automated backups:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: telegram-backup
  namespace: telegram-service
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: backup-image:latest
            command: ["/bin/bash", "/backup.sh"]
            env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: telegram-secrets
                  key: database-url
          restartPolicy: OnFailure
```

This deployment guide provides comprehensive instructions for deploying the Telegram service in various environments, from development to production, with proper monitoring, backup, and recovery procedures.
