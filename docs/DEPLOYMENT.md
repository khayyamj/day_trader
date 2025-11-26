# Trading Bot Deployment Guide

Complete guide for deploying the Trading Bot application to a production server.

## Table of Contents

- [Prerequisites](#prerequisites)
- [System Requirements](#system-requirements)
- [Installation Steps](#installation-steps)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Service Installation](#service-installation)
- [Verification](#verification)
- [Monitoring](#monitoring)
- [Backup and Restore](#backup-and-restore)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Python 3.9+**: Backend runtime
- **Node.js 18+**: Frontend build and runtime
- **PostgreSQL 14+**: Primary database
- **Redis 6+**: Cache and session store (optional)
- **Interactive Brokers TWS/Gateway**: For live trading

### Required Accounts

- **Interactive Brokers** account (Paper or Live)
  - TWS or IB Gateway installed and configured
  - API access enabled
- **Twelve Data** API key for market data
- **Email account** for SMTP notifications (Gmail recommended)

### Server Requirements

- **OS**: Ubuntu 20.04+ or similar Linux distribution
- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 20GB minimum free space
- **Network**: Stable internet connection with access to:
  - IBKR servers (port 7496/7497 for TWS, 4001/4002 for Gateway)
  - Market data APIs
  - SMTP server (port 587 for TLS)

## System Requirements

### Port Requirements

The following ports need to be available:

- **8000**: Backend API server
- **3000**: Frontend development server (optional)
- **5432**: PostgreSQL (can be remote)
- **6379**: Redis (can be remote)
- **7497**: IBKR TWS Paper trading
- **7496**: IBKR TWS Live trading
- **4002**: IBKR Gateway Paper trading
- **4001**: IBKR Gateway Live trading

## Installation Steps

### 1. Create Application User

```bash
sudo useradd -r -m -d /opt/trading-bot -s /bin/bash trading
sudo passwd trading  # Set a strong password
```

### 2. Clone Repository

```bash
sudo -u trading bash
cd /opt/trading-bot
git clone https://github.com/yourusername/trading-bot.git .
```

### 3. Install Backend Dependencies

```bash
cd /opt/trading-bot/backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies

```bash
cd /opt/trading-bot/frontend

# Install Node.js dependencies
npm install

# Build production bundle
npm run build
```

## Configuration

### 1. Environment Variables

Create `.env` file in the project root:

```bash
cd /opt/trading-bot
cp .env.example .env
nano .env
```

Configure the following variables:

```bash
# Database
DATABASE_URL=postgresql://trading_user:secure_password@localhost:5432/trading_db

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# API Keys
TWELVE_DATA_API_KEY=your_twelve_data_api_key

# Interactive Brokers
IBKR_USERNAME=your_ibkr_username
IBKR_PASSWORD=your_ibkr_password
IBKR_TRADING_MODE=paper  # or 'live'
IBKR_PORT=7497  # 7496 for live, 7497 for paper

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=False

# Security
SECRET_KEY=generate_a_secure_random_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
BACKEND_CORS_ORIGINS=["http://your-domain.com"]

# Email/SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_specific_password
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=your_email@gmail.com
```

**Important**:
- Generate a secure `SECRET_KEY`: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833)
- Keep `.env` file secure with `chmod 600 .env`

### 2. File Permissions

```bash
# Set ownership
sudo chown -R trading:trading /opt/trading-bot

# Secure .env file
chmod 600 /opt/trading-bot/.env

# Make scripts executable
chmod +x /opt/trading-bot/deploy/setup.sh
```

## Database Setup

### 1. Install PostgreSQL

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

### 2. Create Database and User

```bash
sudo -u postgres psql

# In PostgreSQL prompt:
CREATE USER trading_user WITH PASSWORD 'secure_password';
CREATE DATABASE trading_db OWNER trading_user;
GRANT ALL PRIVILEGES ON DATABASE trading_db TO trading_user;
\q
```

### 3. Run Migrations

```bash
cd /opt/trading-bot/backend
source venv/bin/activate

# Run Alembic migrations
alembic upgrade head
```

### 4. Initialize Data

```bash
# Add initial watchlist stocks
python -m app.scripts.init_stocks

# Verify database
python -m app.scripts.check_db
```

## Service Installation

### 1. Install systemd Service

```bash
cd /opt/trading-bot/deploy
sudo ./setup.sh
```

This script will:
- Create necessary directories and users
- Install systemd service file
- Enable automatic startup

### 2. Start Service

```bash
sudo systemctl start trading-bot
sudo systemctl status trading-bot
```

### 3. Enable Auto-Start on Boot

```bash
sudo systemctl enable trading-bot
```

## Verification

### 1. Check Service Status

```bash
# Service status
sudo systemctl status trading-bot

# View logs
sudo journalctl -u trading-bot -f

# Application logs
tail -f /var/log/trading-bot/app.log
```

### 2. Test API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Detailed health
curl http://localhost:8000/api/health

# API documentation
open http://localhost:8000/docs
```

### 3. Verify Database Connection

```bash
curl http://localhost:8000/api/health/database
```

### 4. Verify Broker Connection

```bash
# Make sure TWS or IB Gateway is running first
curl http://localhost:8000/api/health/broker
```

## Monitoring

### 1. Health Check Endpoints

- **Overall Health**: `GET /api/health`
- **Detailed Metrics**: `GET /api/health/detailed`
- **Database**: `GET /api/health/database`
- **Broker**: `GET /api/health/broker`
- **Scheduler**: `GET /api/health/scheduler`
- **Disk Space**: `GET /api/health/disk`

### 2. View Logs

```bash
# Real-time application logs
tail -f /var/log/trading-bot/app.log

# Real-time error logs
tail -f /var/log/trading-bot/error.log

# systemd logs
sudo journalctl -u trading-bot -f

# Last 100 lines
sudo journalctl -u trading-bot -n 100
```

### 3. Email Notifications

The system sends automated emails for:
- Trade executions
- Risk warnings
- System errors
- Daily trading summaries (4:30 PM ET)
- Recovery reports

### 4. Event Logging

Query events via API:

```bash
# Recent events
curl http://localhost:8000/api/events?hours=24

# Events by type
curl "http://localhost:8000/api/events?event_type=TRADE&hours=24"

# Events summary
curl http://localhost:8000/api/events/summary
```

## Backup and Restore

### Database Backup

#### Create Backup

```bash
# Create backup directory
sudo mkdir -p /var/backups/trading-bot
sudo chown trading:trading /var/backups/trading-bot

# Manual backup
sudo -u postgres pg_dump trading_db > /var/backups/trading-bot/backup_$(date +%Y%m%d_%H%M%S).sql
```

#### Automated Daily Backup

Create backup script:

```bash
#!/bin/bash
# /opt/trading-bot/scripts/backup.sh

BACKUP_DIR="/var/backups/trading-bot"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql"

# Create backup
sudo -u postgres pg_dump trading_db > "$BACKUP_FILE"

# Compress
gzip "$BACKUP_FILE"

# Delete backups older than 30 days
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

Add to cron:

```bash
sudo crontab -e

# Add line:
0 2 * * * /opt/trading-bot/scripts/backup.sh
```

#### Restore from Backup

```bash
# Stop service
sudo systemctl stop trading-bot

# Restore database
gunzip -c /var/backups/trading-bot/backup_YYYYMMDD_HHMMSS.sql.gz | sudo -u postgres psql trading_db

# Start service
sudo systemctl start trading-bot
```

### Configuration Backup

```bash
# Backup .env and configs
cp /opt/trading-bot/.env /var/backups/trading-bot/env_$(date +%Y%m%d).bak
```

## Troubleshooting

### Service Won't Start

1. Check service status:
   ```bash
   sudo systemctl status trading-bot
   ```

2. View detailed logs:
   ```bash
   sudo journalctl -u trading-bot -n 50 --no-pager
   ```

3. Common issues:
   - **Database connection failed**: Check PostgreSQL is running and credentials are correct
   - **Port already in use**: Another service using port 8000
   - **Permission denied**: Check file ownership and permissions
   - **Module not found**: Ensure virtual environment has all dependencies

### Database Connection Issues

```bash
# Test PostgreSQL connection
sudo -u postgres psql -d trading_db -c "SELECT 1"

# Check PostgreSQL status
sudo systemctl status postgresql

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Broker Connection Issues

1. Verify IBKR TWS/Gateway is running
2. Check TWS API settings:
   - File > Global Configuration > API > Settings
   - Enable ActiveX and Socket Clients
   - Port: 7497 (paper) or 7496 (live)
   - Trusted IP: 127.0.0.1

3. Test connection:
   ```bash
   curl http://localhost:8000/api/health/broker
   ```

### High Memory Usage

```bash
# Check memory usage
curl http://localhost:8000/api/health/detailed | jq '.metrics.process'

# Restart service
sudo systemctl restart trading-bot
```

### View Crash Recovery Reports

```bash
# Check recovery events in database
psql -U trading_user -d trading_db -c "SELECT * FROM recovery_events ORDER BY timestamp DESC LIMIT 5;"
```

## Security Checklist

- [ ] Strong passwords for database and system users
- [ ] `.env` file secured with `chmod 600`
- [ ] Firewall configured (UFW or iptables)
- [ ] SSH key-based authentication enabled
- [ ] Fail2ban installed for brute-force protection
- [ ] Regular security updates applied
- [ ] Database backups automated
- [ ] SSL/TLS for production web interface
- [ ] IBKR credentials never logged or exposed

## Updates and Maintenance

### Update Application

```bash
# Stop service
sudo systemctl stop trading-bot

# Backup current version
sudo -u trading bash
cd /opt/trading-bot
git stash  # Save local changes
git pull origin main

# Update dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Run migrations
alembic upgrade head

# Restart service
sudo systemctl start trading-bot
```

### Monitor Disk Space

```bash
# Check disk usage
df -h

# Check application directory
du -sh /opt/trading-bot

# Clean old logs
find /var/log/trading-bot -name "*.log" -mtime +30 -delete
```

## Support

For issues and support:
- GitHub Issues: https://github.com/yourusername/trading-bot/issues
- Email: support@yourdomain.com
- Documentation: https://docs.yourdomain.com
