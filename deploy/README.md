# Trading Bot Deployment Files

This directory contains files for deploying the Trading Bot as a systemd service with automatic restart capabilities.

## Files

- `trading-bot.service` - systemd service configuration file
- `setup.sh` - Automated deployment setup script

## Quick Start

### 1. Run Setup Script

```bash
cd deploy
sudo ./setup.sh
```

This will:
- Create a dedicated `trading` user
- Set up log directories
- Install the systemd service
- Enable the service for automatic startup

### 2. Deploy Application

Copy your application to `/opt/trading-bot`:

```bash
sudo cp -r /path/to/your/Trading /opt/trading-bot
sudo chown -R trading:trading /opt/trading-bot
```

### 3. Configure Environment

Set up your `.env` file:

```bash
sudo cp /opt/trading-bot/.env.example /opt/trading-bot/.env
sudo nano /opt/trading-bot/.env
# Configure your SMTP, database, IBKR credentials, etc.
```

### 4. Install Dependencies

```bash
sudo -u trading bash
cd /opt/trading-bot/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
exit
```

### 5. Start Service

```bash
sudo systemctl start trading-bot
sudo systemctl status trading-bot
```

## Service Management

### Start/Stop/Restart

```bash
sudo systemctl start trading-bot
sudo systemctl stop trading-bot
sudo systemctl restart trading-bot
```

### Check Status

```bash
sudo systemctl status trading-bot
```

### View Logs

```bash
# Real-time systemd logs
sudo journalctl -u trading-bot -f

# Application logs
tail -f /var/log/trading-bot/app.log

# Error logs
tail -f /var/log/trading-bot/error.log
```

### Enable/Disable Auto-Start

```bash
# Enable (already done by setup.sh)
sudo systemctl enable trading-bot

# Disable
sudo systemctl disable trading-bot
```

## Auto-Restart Configuration

The service is configured with the following restart policies:

- **Restart Policy**: `always` - Service will restart on any failure
- **Restart Delay**: `10s` - Wait 10 seconds before restarting
- **Restart Limits**: Max 5 restarts within 10 minutes
  - If the service fails 5 times within 10 minutes, systemd will stop trying
  - This prevents infinite restart loops

### Testing Auto-Restart

1. **Test normal restart**:
   ```bash
   # Kill the process
   sudo systemctl kill -s SIGTERM trading-bot

   # Check if it restarts (should restart within 10 seconds)
   watch sudo systemctl status trading-bot
   ```

2. **Test restart limits**:
   ```bash
   # Cause rapid failures (simulate crashes)
   for i in {1..6}; do
       sudo systemctl kill -s SIGKILL trading-bot
       sleep 1
   done

   # Check status (should show "start-limit-hit" after 5th failure)
   sudo systemctl status trading-bot

   # Reset the restart counter
   sudo systemctl reset-failed trading-bot
   sudo systemctl start trading-bot
   ```

## Troubleshooting

### Service Won't Start

1. Check logs:
   ```bash
   sudo journalctl -u trading-bot -n 50
   ```

2. Verify file permissions:
   ```bash
   ls -la /opt/trading-bot
   ```

3. Check environment file:
   ```bash
   sudo cat /opt/trading-bot/.env
   ```

4. Test manually:
   ```bash
   sudo -u trading bash
   cd /opt/trading-bot/backend
   source venv/bin/activate
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

### Service Keeps Restarting

1. Check error logs:
   ```bash
   tail -f /var/log/trading-bot/error.log
   ```

2. Check for configuration issues:
   - Database connection
   - IBKR credentials
   - API keys

3. Verify dependencies are installed:
   ```bash
   sudo -u trading bash
   cd /opt/trading-bot/backend
   source venv/bin/activate
   pip list
   ```

### Reset Service After Restart Limit Hit

```bash
sudo systemctl reset-failed trading-bot
sudo systemctl start trading-bot
```

## Security Notes

- Service runs as dedicated `trading` user (not root)
- `NoNewPrivileges=true` prevents privilege escalation
- `PrivateTmp=true` provides isolated /tmp directory
- Memory limited to 2GB max
- File descriptor limit: 65536

## Service Dependencies

The service requires:
- `postgresql.service` - Database
- `redis.service` - Cache/message broker (if used)
- `network.target` - Network connectivity

Make sure these services are running:

```bash
sudo systemctl status postgresql
sudo systemctl status redis
```
