# Deployment Guide

## Overview

This guide covers deployment strategies for the URL Watcher with TextBelt SMS notifications, from simple local installations to production-ready cloud deployments.

## Table of Contents

- [Local Development Setup](#local-development-setup)
- [Single Server Deployment](#single-server-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Container Deployment](#container-deployment)
- [Production Considerations](#production-considerations)
- [Monitoring and Logging](#monitoring-and-logging)

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

4. **Configure SMS Notifications**
   ```bash
   # Create .env file with your TextBelt credentials
   cat > .env << EOF
   SMS_PHONE_NUMBER=+1234567890
   TEXTBELT_API_KEY=your_textbelt_api_key
   EOF
   ```

5. **Verify Installation**
   ```bash
   python url_watcher.py --help
   python test_textbelt.py  # Test SMS functionality
   ```

### Development Configuration

Create a development configuration file:

```bash
# dev_config.sh
export SMS_PHONE_NUMBER="+1234567890"
export TEXTBELT_API_KEY="your_dev_api_key"
export LOG_LEVEL="DEBUG"
export URL_WATCHER_ENV="development"
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
- TextBelt API account and key

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
   cat > /home/urlwatcher/watcher/.env << EOF
   SMS_PHONE_NUMBER=+1234567890
   TEXTBELT_API_KEY=your_production_api_key
   LOG_LEVEL=INFO
   EOF
   
   chmod 600 /home/urlwatcher/watcher/.env
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

```python
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

Update systemd service:
```bash
# Update ExecStart in /etc/systemd/system/urlwatcher.service
ExecStart=/home/urlwatcher/watcher/.venv/bin/python /home/urlwatcher/watcher/multi_monitor.py
```

## Cloud Deployment

### DigitalOcean Droplet

1. **Create Droplet**
   ```bash
   # Using DigitalOcean CLI
   doctl compute droplet create urlwatcher \
     --image ubuntu-20-04-x64 \
     --size s-1vcpu-1gb \
     --region nyc1 \
     --ssh-keys your-ssh-key-id \
     --user-data-file user-data.sh
   ```

2. **User Data Script** (`user-data.sh`):
   ```bash
   #!/bin/bash
   apt update && apt upgrade -y
   apt install -y python3 python3-pip python3-venv git
   
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
   
   # Create systemd service and start
   systemctl enable urlwatcher
   systemctl start urlwatcher
   ```

### Heroku Deployment

1. **Create Procfile**
   ```
   worker: python url_watcher.py $TARGET_URL --continuous --sms
   ```

2. **Configure Environment Variables**
   ```bash
   heroku config:set SMS_PHONE_NUMBER="+1234567890"
   heroku config:set TEXTBELT_API_KEY="your_api_key"
   heroku config:set TARGET_URL="https://example.com"
   ```

3. **Deploy**
   ```bash
   git add .
   git commit -m "Add Heroku deployment"
   git push heroku main
   heroku ps:scale worker=1
   ```

### Railway Deployment

1. **Create railway.json**
   ```json
   {
     "$schema": "https://railway.app/railway.schema.json",
     "build": {
       "builder": "NIXPACKS"
     },
     "deploy": {
       "startCommand": "python url_watcher.py $TARGET_URL --continuous --sms",
       "healthcheckPath": "/health",
       "healthcheckTimeout": 100,
       "restartPolicyType": "ON_FAILURE"
     }
   }
   ```

2. **Environment Variables**
   Set in Railway dashboard:
   - `SMS_PHONE_NUMBER`: Your phone number
   - `TEXTBELT_API_KEY`: Your TextBelt API key  
   - `TARGET_URL`: URL to monitor

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
CMD ["python", "url_watcher.py", "https://httpbin.org/uuid", "--continuous", "--sms"]
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
      - SMS_PHONE_NUMBER=${SMS_PHONE_NUMBER}
      - TEXTBELT_API_KEY=${TEXTBELT_API_KEY}
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
        - name: SMS_PHONE_NUMBER
          valueFrom:
            secretKeyRef:
              name: textbelt-credentials
              key: phone-number
        - name: TEXTBELT_API_KEY
          valueFrom:
            secretKeyRef:
              name: textbelt-credentials
              key: api-key
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Secret
metadata:
  name: textbelt-credentials
type: Opaque
data:
  phone-number: <base64-encoded-phone-number>
  api-key: <base64-encoded-api-key>
```

## Production Considerations

### Security

1. **Secrets Management**
   ```bash
   # Use secure secret storage
   # For example, with HashiCorp Vault:
   vault kv put secret/urlwatcher \
     sms_phone_number="+1234567890" \
     textbelt_api_key="your_key"
   ```

2. **Network Security**
   - Use firewalls to restrict access
   - Enable HTTPS for monitoring interfaces
   - Use VPN for administrative access

3. **File Permissions**
   ```bash
   # Secure configuration files
   chmod 600 /home/urlwatcher/watcher/.env
   chown urlwatcher:urlwatcher /home/urlwatcher/watcher/.env
   ```

### Performance Optimization

1. **Connection Pooling**
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

2. **Rate Limiting**
   ```python
   # Respect TextBelt rate limits
   import time
   from functools import wraps
   
   class RateLimitedSMSNotifier(SMSNotifier):
       def __init__(self, *args, **kwargs):
           super().__init__(*args, **kwargs)
           self.last_sms_time = 0
           self.min_interval = 60  # Minimum 1 minute between SMS
       
       def send_notification(self, url, message, subject=None):
           # Enforce rate limiting
           current_time = time.time()
           time_since_last = current_time - self.last_sms_time
           
           if time_since_last < self.min_interval:
               sleep_time = self.min_interval - time_since_last
               time.sleep(sleep_time)
           
           result = super().send_notification(url, message, subject)
           self.last_sms_time = time.time()
           return result
   ```

### Monitoring and Alerting

1. **Health Check Endpoint**
   ```python
   from flask import Flask, jsonify
   
   app = Flask(__name__)
   
   @app.route('/health')
   def health_check():
       """Health check endpoint"""
       try:
           # Test TextBelt configuration
           notifier = create_notifier_from_env()
           is_configured = notifier.is_configured()
           
           return jsonify({
               'status': 'healthy' if is_configured else 'degraded',
               'sms_configured': is_configured,
               'timestamp': time.time()
           }), 200 if is_configured else 503
       except Exception as e:
           return jsonify({
               'status': 'unhealthy',
               'error': str(e)
           }), 503
   
   @app.route('/metrics')
   def metrics():
       """Prometheus metrics endpoint"""
       # Return metrics in Prometheus format
       return "# HELP urlwatcher_checks_total Total URL checks\n" \
              "urlwatcher_checks_total 42\n"
   ```

### Backup and Recovery

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

# Backup configuration (excluding secrets)
cp /home/urlwatcher/watcher/.env.example "$BACKUP_DIR/config_template_$DATE.env"

# Upload to cloud storage (example with rclone)
rclone copy "$BACKUP_DIR/cache_backup_$DATE.tar.gz" remote:urlwatcher-backups/

# Clean old backups (keep last 30 days)  
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
```

## Environment Variables Reference

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `SMS_PHONE_NUMBER` | Target phone number in E.164 format | `+1234567890` | Yes |
| `TEXTBELT_API_KEY` | TextBelt API key | `textbelt_abc123...` | Yes |
| `LOG_LEVEL` | Logging level | `INFO`, `DEBUG` | No |
| `URL_WATCHER_ENV` | Environment name | `production`, `development` | No |

This deployment guide focuses on TextBelt integration and removes all AWS dependencies, providing modern, cloud-agnostic deployment options.