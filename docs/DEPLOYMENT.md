# Deployment Guide

## Overview

This guide covers various deployment strategies for the URL Watcher, from simple local installations to production-ready cloud deployments with high availability and monitoring.

## Table of Contents

- [Local Development Setup](#local-development-setup)
- [Single Server Deployment](#single-server-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Container Deployment](#container-deployment)
- [Production Considerations](#production-considerations)
- [Monitoring and Logging](#monitoring-and-logging)
- [Backup and Recovery](#backup-and-recovery)

## Local Development Setup

### Quick Start

1. **Clone Repository**
   ```bash
   git clone https://github.com/smarks/watcher.git
   cd watcher
   ```

2. **Setup Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify Installation**
   ```bash
   python url_watcher.py --help
   ```

### Development Configuration

Create a development configuration file:

```bash
# dev_config.sh
export AWS_REGION="us-east-1"
export SNS_TOPIC_ARN="arn:aws:sns:us-east-1:123456789012:dev-topic"
export AWS_ACCESS_KEY_ID="your-dev-key"
export AWS_SECRET_ACCESS_KEY="your-dev-secret"

# Development-specific settings
export URL_WATCHER_ENV="development"
export LOG_LEVEL="DEBUG"
```

Load configuration:
```bash
source dev_config.sh
python url_watcher.py https://httpbin.org/uuid --sms
```

## Single Server Deployment

### Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- Python 3.7 or higher
- systemd for service management
- (Optional) nginx for reverse proxy
- (Optional) AWS CLI for SMS functionality

### Installation Steps

1. **Update System**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install python3 python3-pip python3-venv git -y
   ```

2. **Create Service User**
   ```bash
   sudo useradd --system --create-home --shell /bin/bash urlwatcher
   sudo su - urlwatcher
   ```

3. **Install Application**
   ```bash
   git clone https://github.com/smarks/watcher.git
   cd watcher
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Create Configuration**
   ```bash
   # Create production config
   cat > /home/urlwatcher/watcher/production.env << EOF
   AWS_REGION=us-east-1
   SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:production-topic
   AWS_ACCESS_KEY_ID=your-production-key
   AWS_SECRET_ACCESS_KEY=your-production-secret
   LOG_LEVEL=INFO
   EOF
   
   chmod 600 /home/urlwatcher/watcher/production.env
   ```

5. **Create Systemd Service**
   ```bash
   sudo tee /etc/systemd/system/urlwatcher.service << EOF
   [Unit]
   Description=URL Watcher Service
   After=network.target
   Wants=network.target
   
   [Service]
   Type=simple
   User=urlwatcher
   Group=urlwatcher
   WorkingDirectory=/home/urlwatcher/watcher
   Environment=PATH=/home/urlwatcher/watcher/.venv/bin
   EnvironmentFile=/home/urlwatcher/watcher/production.env
   ExecStart=/home/urlwatcher/watcher/.venv/bin/python url_watcher.py https://example.com --continuous --sms
   Restart=always
   RestartSec=30
   StandardOutput=journal
   StandardError=journal
   
   [Install]
   WantedBy=multi-user.target
   EOF
   ```

6. **Start Service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable urlwatcher
   sudo systemctl start urlwatcher
   sudo systemctl status urlwatcher
   ```

### Multiple URL Monitoring

For monitoring multiple URLs, create a wrapper script:

```bash
# /home/urlwatcher/watcher/multi_monitor.py
#!/usr/bin/env python3
"""
Multi-URL monitoring service
"""
import os
import time
import logging
import threading
from url_watcher import URLWatcher
from sms_notifier import create_notifier_from_env

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/urlwatcher/urlwatcher.log'),
        logging.StreamHandler()
    ]
)

def monitor_url(url, interval_min=60, interval_max=300):
    """Monitor a single URL in a separate thread"""
    logger = logging.getLogger(f'monitor-{url}')
    
    try:
        sms_notifier = create_notifier_from_env()
        watcher = URLWatcher(
            storage_file=f"/home/urlwatcher/data/{url.replace('://', '_').replace('/', '_')}.json",
            sms_notifier=sms_notifier
        )
        
        watcher.watch_continuously(url, interval_min, interval_max)
    except Exception as e:
        logger.error(f"Error monitoring {url}: {e}")

def main():
    """Main monitoring service"""
    urls = [
        "https://example.com",
        "https://httpbin.org/uuid",
        "https://api.github.com/zen"
    ]
    
    # Create data directory
    os.makedirs("/home/urlwatcher/data", exist_ok=True)
    
    # Start monitoring threads
    threads = []
    for url in urls:
        thread = threading.Thread(target=monitor_url, args=(url,), daemon=True)
        thread.start()
        threads.append(thread)
        time.sleep(1)  # Stagger starts
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(60)
            # Check thread health
            for i, thread in enumerate(threads):
                if not thread.is_alive():
                    logging.warning(f"Thread {i} died, restarting...")
                    new_thread = threading.Thread(
                        target=monitor_url, 
                        args=(urls[i],), 
                        daemon=True
                    )
                    new_thread.start()
                    threads[i] = new_thread
    except KeyboardInterrupt:
        logging.info("Shutting down URL Watcher service")

if __name__ == "__main__":
    main()
```

Update systemd service to use the wrapper:
```bash
# Update ExecStart in /etc/systemd/system/urlwatcher.service
ExecStart=/home/urlwatcher/watcher/.venv/bin/python /home/urlwatcher/watcher/multi_monitor.py
```

## Cloud Deployment

### AWS EC2 Deployment

#### Launch EC2 Instance

1. **Launch Instance**
   ```bash
   # Using AWS CLI
   aws ec2 run-instances \
     --image-id ami-0c02fb55956c7d316 \
     --instance-type t3.micro \
     --key-name your-key-pair \
     --security-group-ids sg-xxxxxxxx \
     --subnet-id subnet-xxxxxxxx \
     --user-data file://user-data.sh \
     --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=URLWatcher}]'
   ```

2. **User Data Script** (`user-data.sh`):
   ```bash
   #!/bin/bash
   yum update -y
   yum install -y python3 python3-pip git
   
   # Create service user
   useradd --system --create-home --shell /bin/bash urlwatcher
   
   # Install application
   sudo -u urlwatcher bash << 'EOF'
   cd /home/urlwatcher
   git clone https://github.com/smarks/watcher.git
   cd watcher
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   EOF
   
   # Create systemd service (similar to above)
   # ... service configuration ...
   
   systemctl enable urlwatcher
   systemctl start urlwatcher
   ```

#### IAM Role Configuration

Create IAM role for EC2 instance:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": "arn:aws:sns:*:*:url-watcher-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

### AWS Lambda Deployment

For serverless URL checking:

```python
# lambda_function.py
import json
import boto3
from url_watcher import URLWatcher
from sms_notifier import SMSNotifier

def lambda_handler(event, context):
    """Lambda function for URL monitoring"""
    
    # Get configuration from environment variables
    topic_arn = os.environ['SNS_TOPIC_ARN']
    urls = json.loads(os.environ['URLS_TO_MONITOR'])
    
    # Initialize components
    sms_notifier = SMSNotifier(topic_arn=topic_arn)
    watcher = URLWatcher(sms_notifier=sms_notifier)
    
    results = []
    
    for url in urls:
        try:
            changed, diff = watcher.check_url(url)
            results.append({
                'url': url,
                'changed': changed,
                'success': True
            })
        except Exception as e:
            results.append({
                'url': url,
                'error': str(e),
                'success': False
            })
    
    return {
        'statusCode': 200,
        'body': json.dumps(results)
    }
```

**Deployment Package**:
```bash
# Create deployment package
mkdir lambda-deployment
cd lambda-deployment
pip install -r ../requirements.txt -t .
cp ../url_watcher.py ../sms_notifier.py .
cp lambda_function.py .
zip -r urlwatcher-lambda.zip .
```

**CloudFormation Template**:
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  URLWatcherFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: url-watcher
      Runtime: python3.9
      Handler: lambda_function.lambda_handler
      Code:
        ZipFile: |
          # Deployment package content
      Environment:
        Variables:
          SNS_TOPIC_ARN: !Ref URLWatcherTopic
          URLS_TO_MONITOR: '["https://example.com", "https://httpbin.org/uuid"]'
      Role: !GetAtt LambdaExecutionRole.Arn
      Timeout: 300

  ScheduleRule:
    Type: AWS::Events::Rule
    Properties:
      Description: "Trigger URL Watcher every 5 minutes"
      ScheduleExpression: "rate(5 minutes)"
      State: ENABLED
      Targets:
        - Arn: !GetAtt URLWatcherFunction.Arn
          Id: "URLWatcherTarget"
```

### Google Cloud Platform

#### Cloud Run Deployment

1. **Create Dockerfile**:
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY . .
   
   CMD ["python", "cloud_run_service.py"]
   ```

2. **Cloud Run Service** (`cloud_run_service.py`):
   ```python
   import os
   from flask import Flask, jsonify
   from url_watcher import URLWatcher
   
   app = Flask(__name__)
   
   @app.route('/check', methods=['POST'])
   def check_urls():
       """HTTP endpoint for URL checking"""
       urls = request.json.get('urls', [])
       watcher = URLWatcher()
       
       results = []
       for url in urls:
           try:
               changed, diff = watcher.check_url(url)
               results.append({
                   'url': url,
                   'changed': changed,
                   'diff': diff
               })
           except Exception as e:
               results.append({
                   'url': url,
                   'error': str(e)
               })
       
       return jsonify(results)
   
   if __name__ == '__main__':
       port = int(os.environ.get('PORT', 8080))
       app.run(host='0.0.0.0', port=port)
   ```

3. **Deploy to Cloud Run**:
   ```bash
   # Build and deploy
   gcloud run deploy url-watcher \
     --source . \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

## Container Deployment

### Docker

#### Basic Dockerfile

```dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash urlwatcher
RUN chown -R urlwatcher:urlwatcher /app
USER urlwatcher

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "from url_watcher import URLWatcher; URLWatcher()" || exit 1

# Default command
CMD ["python", "url_watcher.py", "https://httpbin.org/uuid", "--continuous"]
```

#### Multi-stage Build

```dockerfile
# Build stage
FROM python:3.9-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.9-slim

# Copy Python packages from builder stage
COPY --from=builder /root/.local /root/.local

# Add user packages to PATH
ENV PATH=/root/.local/bin:$PATH

WORKDIR /app
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash urlwatcher
RUN chown -R urlwatcher:urlwatcher /app
USER urlwatcher

CMD ["python", "url_watcher.py", "https://httpbin.org/uuid", "--continuous"]
```

#### Docker Compose

```yaml
version: '3.8'

services:
  urlwatcher:
    build: .
    container_name: urlwatcher
    restart: unless-stopped
    environment:
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - SNS_TOPIC_ARN=${SNS_TOPIC_ARN}
      - AWS_REGION=us-east-1
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    command: ["python", "multi_monitor.py"]
    
  # Optional: Add monitoring
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-storage:/var/lib/grafana

volumes:
  grafana-storage:
```

### Kubernetes

#### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: urlwatcher
  labels:
    app: urlwatcher
spec:
  replicas: 2
  selector:
    matchLabels:
      app: urlwatcher
  template:
    metadata:
      labels:
        app: urlwatcher
    spec:
      containers:
      - name: urlwatcher
        image: urlwatcher:latest
        env:
        - name: AWS_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: aws-credentials
              key: access-key-id
        - name: AWS_SECRET_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: aws-credentials
              key: secret-access-key
        - name: SNS_TOPIC_ARN
          value: "arn:aws:sns:us-east-1:123456789012:urlwatcher"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
        livenessProbe:
          exec:
            command:
            - python
            - -c
            - "from url_watcher import URLWatcher; URLWatcher()"
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          exec:
            command:
            - python
            - -c
            - "from url_watcher import URLWatcher; URLWatcher()"
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Secret
metadata:
  name: aws-credentials
type: Opaque
data:
  access-key-id: <base64-encoded-access-key>
  secret-access-key: <base64-encoded-secret-key>
```

#### Helm Chart

Create `Chart.yaml`:
```yaml
apiVersion: v2
name: urlwatcher
description: URL Watcher Helm Chart
version: 0.1.0
appVersion: "1.0"
```

Create `values.yaml`:
```yaml
replicaCount: 2

image:
  repository: urlwatcher
  tag: latest
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 8080

resources:
  limits:
    cpu: 500m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi

aws:
  accessKeyId: ""
  secretAccessKey: ""
  region: us-east-1
  snsTopicArn: ""

urls:
  - https://example.com
  - https://httpbin.org/uuid
```

## Production Considerations

### Security

1. **Secrets Management**
   ```bash
   # Use AWS Secrets Manager
   aws secretsmanager create-secret \
     --name urlwatcher/production \
     --description "URL Watcher production secrets" \
     --secret-string '{"aws_access_key_id":"xxx","aws_secret_access_key":"xxx","sns_topic_arn":"xxx"}'
   ```

2. **Network Security**
   - Use security groups/firewalls to restrict access
   - Enable HTTPS for all web interfaces
   - Use VPN for administrative access

3. **File Permissions**
   ```bash
   # Secure configuration files
   chmod 600 /home/urlwatcher/watcher/production.env
   chown urlwatcher:urlwatcher /home/urlwatcher/watcher/production.env
   ```

### Performance Optimization

1. **Resource Monitoring**
   ```python
   # Add resource monitoring to your service
   import psutil
   import logging
   
   def monitor_resources():
       cpu_percent = psutil.cpu_percent()
       memory_percent = psutil.virtual_memory().percent
       
       if cpu_percent > 80:
           logging.warning(f"High CPU usage: {cpu_percent}%")
       if memory_percent > 80:
           logging.warning(f"High memory usage: {memory_percent}%")
   ```

2. **Connection Pooling**
   ```python
   # Use requests session for connection pooling
   import requests
   from requests.adapters import HTTPAdapter
   
   class OptimizedURLWatcher(URLWatcher):
       def __init__(self, **kwargs):
           super().__init__(**kwargs)
           self.session = requests.Session()
           adapter = HTTPAdapter(pool_connections=10, pool_maxsize=20)
           self.session.mount('http://', adapter)
           self.session.mount('https://', adapter)
       
       def _fetch_url_content(self, url):
           response = self.session.get(url, timeout=10)
           response.raise_for_status()
           return response.text
   ```

### High Availability

1. **Load Balancing**
   ```bash
   # nginx load balancer configuration
   upstream urlwatcher_backend {
       server 10.0.1.10:8080;
       server 10.0.1.11:8080;
       server 10.0.1.12:8080;
   }
   
   server {
       listen 80;
       location / {
           proxy_pass http://urlwatcher_backend;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

2. **Database Replication**
   ```python
   # Use distributed cache for URL states
   import redis
   
   class DistributedURLWatcher(URLWatcher):
       def __init__(self, redis_url="redis://localhost:6379", **kwargs):
           super().__init__(**kwargs)
           self.redis_client = redis.from_url(redis_url)
       
       def _load_cache(self):
           try:
               cache_data = self.redis_client.get('urlwatcher_cache')
               if cache_data:
                   return json.loads(cache_data)
           except Exception as e:
               logging.error(f"Redis error: {e}")
           return {}
       
       def _save_cache(self):
           try:
               self.redis_client.set('urlwatcher_cache', json.dumps(self.cache))
           except Exception as e:
               logging.error(f"Redis save error: {e}")
   ```

## Monitoring and Logging

### Centralized Logging

1. **ELK Stack Configuration**
   ```yaml
   # docker-compose.yml for ELK stack
   version: '3.8'
   services:
     elasticsearch:
       image: docker.elastic.co/elasticsearch/elasticsearch:7.15.0
       environment:
         - discovery.type=single-node
       ports:
         - "9200:9200"
     
     logstash:
       image: docker.elastic.co/logstash/logstash:7.15.0
       volumes:
         - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
     
     kibana:
       image: docker.elastic.co/kibana/kibana:7.15.0
       ports:
         - "5601:5601"
       depends_on:
         - elasticsearch
   ```

2. **Structured Logging**
   ```python
   import json
   import logging
   from datetime import datetime
   
   class JSONFormatter(logging.Formatter):
       def format(self, record):
           log_entry = {
               'timestamp': datetime.utcnow().isoformat(),
               'level': record.levelname,
               'logger': record.name,
               'message': record.getMessage(),
               'module': record.module,
               'function': record.funcName,
               'line': record.lineno
           }
           
           if hasattr(record, 'url'):
               log_entry['url'] = record.url
           if hasattr(record, 'changed'):
               log_entry['changed'] = record.changed
               
           return json.dumps(log_entry)
   
   # Configure structured logging
   handler = logging.StreamHandler()
   handler.setFormatter(JSONFormatter())
   logging.getLogger().addHandler(handler)
   ```

### Metrics Collection

1. **Prometheus Metrics**
   ```python
   from prometheus_client import Counter, Histogram, Gauge, start_http_server
   
   # Define metrics
   url_checks_total = Counter('urlwatcher_checks_total', 'Total URL checks', ['url', 'status'])
   url_check_duration = Histogram('urlwatcher_check_duration_seconds', 'URL check duration')
   urls_monitored = Gauge('urlwatcher_urls_monitored', 'Number of URLs being monitored')
   changes_detected = Counter('urlwatcher_changes_detected_total', 'Changes detected', ['url'])
   
   class MetricsURLWatcher(URLWatcher):
       def check_url(self, url):
           with url_check_duration.time():
               try:
                   changed, diff = super().check_url(url)
                   url_checks_total.labels(url=url, status='success').inc()
                   if changed:
                       changes_detected.labels(url=url).inc()
                   return changed, diff
               except Exception as e:
                   url_checks_total.labels(url=url, status='error').inc()
                   raise
   
   # Start metrics server
   start_http_server(8000)
   ```

### Health Checks

```python
from flask import Flask, jsonify
import threading
import time

app = Flask(__name__)
health_status = {'status': 'healthy', 'last_check': None}

def health_monitor():
    """Background health monitoring"""
    while True:
        try:
            # Perform health checks
            watcher = URLWatcher()
            # Test basic functionality
            health_status['status'] = 'healthy'
            health_status['last_check'] = time.time()
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['error'] = str(e)
        
        time.sleep(60)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code

@app.route('/ready')
def readiness_check():
    """Readiness check endpoint"""
    # Check if service is ready to accept requests
    try:
        watcher = URLWatcher()
        return jsonify({'status': 'ready'}), 200
    except Exception as e:
        return jsonify({'status': 'not ready', 'error': str(e)}), 503

# Start health monitoring thread
threading.Thread(target=health_monitor, daemon=True).start()
```

## Backup and Recovery

### Data Backup

```bash
#!/bin/bash
# backup_script.sh

BACKUP_DIR="/var/backups/urlwatcher"
DATA_DIR="/home/urlwatcher/data"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup cache files
tar -czf "$BACKUP_DIR/cache_backup_$DATE.tar.gz" -C "$DATA_DIR" .

# Backup configuration
cp /home/urlwatcher/watcher/production.env "$BACKUP_DIR/config_backup_$DATE.env"

# Upload to S3 (optional)
aws s3 cp "$BACKUP_DIR/cache_backup_$DATE.tar.gz" s3://urlwatcher-backups/

# Clean old backups (keep last 30 days)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
```

### Disaster Recovery

1. **Recovery Script**
   ```bash
   #!/bin/bash
   # recovery_script.sh
   
   BACKUP_S3_BUCKET="urlwatcher-backups"
   RECOVERY_DIR="/tmp/urlwatcher_recovery"
   
   # Download latest backup
   aws s3 sync s3://$BACKUP_S3_BUCKET $RECOVERY_DIR
   
   # Find latest backup
   LATEST_BACKUP=$(ls -t $RECOVERY_DIR/cache_backup_*.tar.gz | head -1)
   
   # Restore data
   sudo systemctl stop urlwatcher
   tar -xzf "$LATEST_BACKUP" -C /home/urlwatcher/data/
   sudo systemctl start urlwatcher
   
   echo "Recovery completed from $LATEST_BACKUP"
   ```

2. **Automated Recovery Testing**
   ```python
   # test_recovery.py
   import subprocess
   import tempfile
   import json
   import os
   
   def test_backup_recovery():
       """Test backup and recovery process"""
       
       # Create test data
       test_cache = {
           "https://test.com": {
               "content": "test content",
               "hash": "testhash",
               "last_checked": "2025-07-29T16:45:32"
           }
       }
       
       with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
           json.dump(test_cache, f)
           test_file = f.name
       
       try:
           # Test backup
           result = subprocess.run(['./backup_script.sh'], capture_output=True, text=True)
           assert result.returncode == 0, f"Backup failed: {result.stderr}"
           
           # Test recovery
           result = subprocess.run(['./recovery_script.sh'], capture_output=True, text=True)
           assert result.returncode == 0, f"Recovery failed: {result.stderr}"
           
           print("✅ Backup/Recovery test passed")
           
       finally:
           os.unlink(test_file)
   
   if __name__ == "__main__":
       test_backup_recovery()
   ```

This deployment guide provides comprehensive coverage of various deployment scenarios, from simple local setups to production-ready cloud deployments with monitoring, logging, and disaster recovery capabilities.