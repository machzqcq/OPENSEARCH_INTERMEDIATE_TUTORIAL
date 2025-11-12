# Deployment Guide

Complete guide for deploying the Generic Ingest & Search application.

## 📋 Pre-Deployment Checklist

### System Requirements

- [ ] Docker 20.10+ installed
- [ ] Docker Compose 2.0+ installed
- [ ] Minimum 4GB RAM available for Docker
- [ ] 10GB free disk space
- [ ] Ports available: 3000, 8000, 9200, 6379

### Optional Requirements

- [ ] OpenAI API key (for Plan-Execute-Reflect agent features)
- [ ] SSL certificates (for production HTTPS)

## 🚀 Deployment Steps

### Step 1: System Preparation

#### Linux
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Set vm.max_map_count for OpenSearch
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
```

#### macOS
```bash
# Install Docker Desktop
brew install --cask docker

# Increase Docker memory to 4GB in Docker Desktop settings
```

#### Windows
```powershell
# Install Docker Desktop from https://www.docker.com/products/docker-desktop
# Increase memory to 4GB in Docker Desktop settings
# Enable WSL 2 backend
```

### Step 2: Project Setup

```bash
# Navigate to project directory
cd "6. REALTIME_PROJECTS/9. generic_ingest_search_app"

# Create environment files
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### Step 3: Configure Environment

#### Root .env
```bash
# Edit main environment file
nano .env
```

**Required:**
```env
SECRET_KEY=your-strong-secret-key-here-minimum-32-chars
```

**Optional (for AI features):**
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
```

#### Backend .env
```bash
nano backend/.env
```

**Configuration:**
```env
OPENSEARCH_HOST=opensearch
OPENSEARCH_PORT=9200
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=Developer@123  # Change for production!

REDIS_HOST=redis
REDIS_PORT=6379

OPENAI_API_KEY=sk-your-key-here
SECRET_KEY=your-secret-key

DEBUG=true  # Set to false for production
```

#### Frontend .env
```bash
nano frontend/.env
```

**Configuration:**
```env
REACT_APP_API_URL=http://localhost:8000
```

For production, use your actual backend URL:
```env
REACT_APP_API_URL=https://api.yourdomain.com
```

### Step 4: Build and Deploy

```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### Step 5: Verify Deployment

```bash
# Check service health
docker-compose ps

# Test backend health
curl http://localhost:8000/health

# Test OpenSearch
curl -k -u admin:Developer@123 https://localhost:9200/_cluster/health

# Test Redis
docker-compose exec redis redis-cli ping
```

Expected output:
```
NAME                   STATUS    PORTS
opensearch            Up        0.0.0.0:9200->9200/tcp
redis                 Up        0.0.0.0:6379->6379/tcp
backend              Up        0.0.0.0:8000->8000/tcp
frontend             Up        0.0.0.0:3000->3000/tcp
```

### Step 6: Access Application

Open browser and navigate to:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

Login with demo credentials:
- Username: `admin`
- Password: `admin123`

## 🔒 Production Deployment

### Security Hardening

#### 1. Change Default Passwords

```env
# In .env and backend/.env
OPENSEARCH_PASSWORD=<strong-password-here>
SECRET_KEY=<32-char-random-string>
```

Generate strong secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### 2. Enable SSL/TLS

Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  backend:
    environment:
      - DEBUG=false
      - OPENSEARCH_USE_SSL=true
      - OPENSEARCH_VERIFY_CERTS=true
  
  frontend:
    environment:
      - REACT_APP_API_URL=https://api.yourdomain.com
```

#### 3. Use Proper Authentication

Replace demo users in `backend/app/core/config.py` with database-backed authentication.

#### 4. Configure Reverse Proxy

Use Nginx or Traefik:

**nginx.conf:**
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Scaling Considerations

#### OpenSearch Cluster

For production, use a multi-node cluster:

```yaml
services:
  opensearch-node1:
    image: opensearchproject/opensearch:2.11.0
    environment:
      - cluster.name=opensearch-cluster
      - node.name=opensearch-node1
      - discovery.seed_hosts=opensearch-node2
      - cluster.initial_cluster_manager_nodes=opensearch-node1,opensearch-node2
  
  opensearch-node2:
    image: opensearchproject/opensearch:2.11.0
    environment:
      - cluster.name=opensearch-cluster
      - node.name=opensearch-node2
      - discovery.seed_hosts=opensearch-node1
      - cluster.initial_cluster_manager_nodes=opensearch-node1,opensearch-node2
```

#### Backend Replicas

Scale backend for high availability:

```bash
docker-compose up -d --scale backend=3
```

Add load balancer configuration.

### Monitoring

#### Health Checks

```bash
# OpenSearch cluster health
curl -k -u admin:password https://localhost:9200/_cluster/health?pretty

# Backend health
curl http://localhost:8000/health

# Container stats
docker stats
```

#### Logging

```bash
# View all logs
docker-compose logs

# Follow specific service
docker-compose logs -f backend

# Save logs to file
docker-compose logs > deployment.log
```

## 🐛 Troubleshooting

### OpenSearch Issues

**Problem**: Container exits immediately
```bash
# Solution: Increase vm.max_map_count
sudo sysctl -w vm.max_map_count=262144
```

**Problem**: Out of memory
```bash
# Solution: Increase Docker memory
# Docker Desktop > Settings > Resources > Memory > 4GB+
```

### Backend Issues

**Problem**: Can't connect to OpenSearch
```bash
# Check OpenSearch is healthy
docker-compose ps opensearch

# Check logs
docker-compose logs opensearch

# Wait for health check
docker-compose logs backend | grep "OpenSearch"
```

**Problem**: Module not found
```bash
# Rebuild backend
docker-compose build backend
docker-compose up -d backend
```

### Frontend Issues

**Problem**: Can't reach backend
```bash
# Check REACT_APP_API_URL in frontend/.env
# Verify CORS settings in backend
docker-compose logs backend | grep CORS
```

**Problem**: Build fails
```bash
# Clean and rebuild
docker-compose down
docker system prune -a
docker-compose up -d --build
```

### Redis Issues

**Problem**: Connection refused
```bash
# Check Redis container
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping
```

## 📊 Monitoring & Maintenance

### Backup

#### OpenSearch Data
```bash
# Backup OpenSearch data volume
docker run --rm -v generic_ingest_search_app_opensearch-data:/data \
  -v $(pwd)/backups:/backup alpine \
  tar czf /backup/opensearch-backup-$(date +%Y%m%d).tar.gz -C /data .
```

#### Redis Data
```bash
# Backup Redis data
docker-compose exec redis redis-cli BGSAVE
docker cp redis:/data/dump.rdb ./backups/redis-backup-$(date +%Y%m%d).rdb
```

### Updates

```bash
# Pull latest images
docker-compose pull

# Rebuild and restart
docker-compose up -d --build

# Clean old images
docker image prune -a
```

### Resource Monitoring

```bash
# Monitor resources
docker stats

# Disk usage
docker system df

# Clean unused resources
docker system prune -a --volumes
```

## 🔄 Rollback Procedure

```bash
# Stop current deployment
docker-compose down

# Restore from backup
# (restore volumes from backup)

# Start previous version
git checkout <previous-commit>
docker-compose up -d --build
```

## 📞 Support

For deployment issues:
1. Check logs: `docker-compose logs`
2. Verify health: `docker-compose ps`
3. Review environment variables
4. Consult README.md and ARCHITECTURE.md

---

**🎉 Deployment Complete!**

Your application is now running at http://localhost:3000
