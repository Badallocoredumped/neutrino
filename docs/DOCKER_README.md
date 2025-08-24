# 🚀 Neutrino Energy Data Pipeline - Docker Deployment Guide

## Overview

The Neutrino Energy Data Pipeline is a production-ready system for monitoring and analyzing Turkey's electricity grid in real-time. This Docker setup provides a complete, containerized environment with all necessary services.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Electricity   │    │     Energy      │    │    MongoDB     │
│   Maps API      │───▶│    Pipeline     │───▶│   (Primary     │
│                 │    │                 │    │    Storage)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   PostgreSQL    │    │    Grafana      │
                       │   (Analytics)   │◀───│  (Dashboards)   │
                       └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- Docker (20.10+)
- Docker Compose (2.0+)
- Electricity Maps API Token ([Get one here](https://app.electricitymaps.com/dashboard))
- 4GB RAM minimum
- 10GB disk space

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd neutrino
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.template .env

# Edit with your configuration
notepad .env  # Windows
# OR
nano .env     # Linux/Mac
```

**Required Configuration:**
- `ELECTRICITY_MAPS_TOKEN`: Your API token
- Database passwords (make them secure!)
- Grafana admin password

### 3. Deploy

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f energy-pipeline

# Check status
docker-compose ps
```

### 4. Access Services

- **Grafana**: http://localhost:3000
  - Username: `admin`
  - Password: (from your .env file)
- **Mongo Express**: http://localhost:8081 (optional)
- **PostgreSQL**: localhost:5432

## 📊 Services

### Energy Pipeline
- **Container**: `neutrino-energy-pipeline`
- **Purpose**: Main ETL application
- **Schedule**: Runs hourly
- **Health Check**: Built-in monitoring

### MongoDB
- **Container**: `neutrino-mongodb`
- **Purpose**: Primary data storage
- **Port**: 27017
- **Data**: Persistent volume

### PostgreSQL
- **Container**: `neutrino-postgres`
- **Purpose**: Analytics database for Grafana
- **Port**: 5432
- **Data**: Persistent volume

### Grafana
- **Container**: `neutrino-grafana`
- **Purpose**: Real-time dashboards
- **Port**: 3000
- **Dashboards**: Auto-configured

### Mongo Express (Optional)
- **Container**: `neutrino-mongo-express`
- **Purpose**: MongoDB web interface
- **Port**: 8081

## 🛠️ Management Commands

### Start/Stop Services
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart energy-pipeline

# Stop and remove everything (including volumes)
docker-compose down -v
```

### Monitoring
```bash
# View logs
docker-compose logs -f [service-name]

# Monitor resource usage
docker stats

# Check health
docker-compose ps
```

### Database Operations
```bash
# Access MongoDB shell
docker-compose exec mongodb mongosh

# Access PostgreSQL
docker-compose exec postgres psql -U neutrino_user -d neutrino_energy

# Backup MongoDB
docker-compose exec mongodb mongodump --out /backup

# Backup PostgreSQL
docker-compose exec postgres pg_dump -U neutrino_user neutrino_energy > backup.sql
```

### Pipeline Operations
```bash
# Run pipeline manually
docker-compose exec energy-pipeline python etl_energy_data.py

# Check pipeline status
docker-compose exec energy-pipeline python -c "
import sys, os
sys.path.append('/app')
from database.energy_data_repository import EnergyDataRepository
repo = EnergyDataRepository()
print(f'Power data count: {repo.get_power_data_count()}')
print(f'Carbon data count: {repo.get_carbon_data_count()}')
"
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```env
# API Configuration
ELECTRICITY_MAPS_TOKEN=your_token_here

# Database Settings
MONGO_USERNAME=neutrino_user
MONGO_PASSWORD=secure_password
POSTGRES_USERNAME=neutrino_user
POSTGRES_PASSWORD=secure_password

# Application Settings
LOG_LEVEL=INFO
PIPELINE_INTERVAL=3600
DATA_RETENTION_DAYS=90
```

### Custom Configuration

1. **Modify Pipeline Frequency**:
   ```env
   PIPELINE_INTERVAL=1800  # 30 minutes
   ```

2. **Change Log Level**:
   ```env
   LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
   ```

3. **Adjust Resource Limits**:
   Edit `docker-compose.yml` memory/CPU limits

## 📊 Grafana Setup

### Initial Dashboard Import

1. Access Grafana at http://localhost:3000
2. Login with your admin credentials
3. Import dashboard:
   - Go to "+" → Import
   - Upload `grafana/dashboards/energy-overview.json`

### Pre-configured Panels

- **Real-time Power Generation**: Current electricity mix
- **Carbon Intensity**: Environmental impact tracking
- **Historical Trends**: 24h/7d/30d comparisons
- **Peak Analysis**: Demand pattern insights
- **Renewable Percentage**: Green energy tracking

## 🔍 Troubleshooting

### Common Issues

1. **Pipeline Not Starting**
   ```bash
   # Check API token
   docker-compose logs energy-pipeline
   
   # Verify environment
   docker-compose exec energy-pipeline env | grep ELECTRICITY_MAPS_TOKEN
   ```

2. **Database Connection Issues**
   ```bash
   # Check database status
   docker-compose ps
   
   # Test connectivity
   docker-compose exec energy-pipeline python -c "
   import pymongo
   client = pymongo.MongoClient('mongodb://mongodb:27017')
   print('MongoDB connected:', client.admin.command('ping'))
   "
   ```

3. **Grafana No Data**
   ```bash
   # Verify PostgreSQL sync
   docker-compose exec postgres psql -U neutrino_user -d neutrino_energy -c "
   SELECT COUNT(*) FROM power_data;
   SELECT COUNT(*) FROM carbon_intensity;
   "
   ```

4. **Memory Issues**
   ```bash
   # Monitor resource usage
   docker stats
   
   # Increase memory limits in docker-compose.yml
   mem_limit: 1g
   ```

### Health Checks

```bash
# Application health
curl http://localhost:8000/health  # If health endpoint implemented

# Database health
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"
docker-compose exec postgres pg_isready -U neutrino_user
```

### Reset Everything

```bash
# Complete reset (WARNING: Destroys all data)
docker-compose down -v
docker system prune -f
docker-compose up -d
```

## 🚀 Production Deployment

### Security Hardening

1. **Change Default Passwords**:
   - Use strong, unique passwords
   - Consider using Docker secrets

2. **Network Security**:
   ```yaml
   # In docker-compose.yml
   ports:
     - "127.0.0.1:3000:3000"  # Bind to localhost only
   ```

3. **SSL/TLS**:
   - Use reverse proxy (nginx/traefik)
   - Implement HTTPS

### Backup Strategy

```bash
# Automated backups
./scripts/backup.sh

# Backup schedule (crontab)
0 2 * * * /path/to/neutrino/scripts/backup.sh
```

### Monitoring

1. **Application Metrics**:
   - Pipeline execution success/failure
   - Data volume trends
   - API response times

2. **Infrastructure Metrics**:
   - Docker container health
   - Database performance
   - Disk usage

### Scaling

```yaml
# Scale specific services
docker-compose up -d --scale energy-pipeline=2
```

## 📝 Development

### Local Development

```bash
# Development with code mounting
docker-compose -f docker-compose.dev.yml up

# Run tests
docker-compose exec energy-pipeline python -m pytest
```

### Code Updates

```bash
# Rebuild after code changes
docker-compose build energy-pipeline
docker-compose up -d energy-pipeline
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test with Docker
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues**: GitHub Issues
- **Documentation**: See `/docs` folder
- **Email**: emirozen@stu.khas.edu.tr

---

**Made with ❤️ for sustainable energy monitoring**
