# Troubleshooting Guide

Common issues and solutions for the Trading Bot application.

## Table of Contents

- [Service Issues](#service-issues)
- [Connection Problems](#connection-problems)
- [Trading Issues](#trading-issues)
- [Performance Issues](#performance-issues)
- [Email Issues](#email-issues)
- [Data Issues](#data-issues)
- [Error Messages](#error-messages)
- [FAQ](#faq)

## Service Issues

### Service Won't Start

**Symptom**: `sudo systemctl start trading-bot` fails or service stops immediately.

**Check:**
```bash
# View service status
sudo systemctl status trading-bot

# View recent logs
sudo journalctl -u trading-bot -n 50 --no-pager

# Check error logs
tail -f /var/log/trading-bot/error.log
```

**Common Causes:**

1. **Database Connection Failed**
   ```bash
   # Test database connection
   psql -U trading_user -d trading_db -c "SELECT 1"

   # If fails, check PostgreSQL is running
   sudo systemctl status postgresql
   sudo systemctl restart postgresql
   ```

2. **Port Already in Use**
   ```bash
   # Check what's using port 8000
   sudo lsof -i :8000

   # Kill the process if needed
   sudo kill -9 <PID>
   ```

3. **Python Dependencies Missing**
   ```bash
   cd /opt/trading-bot/backend
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Permissions Issues**
   ```bash
   # Fix ownership
   sudo chown -R trading:trading /opt/trading-bot

   # Check .env permissions
   ls -la /opt/trading-bot/.env
   chmod 600 /opt/trading-bot/.env
   ```

### Service Keeps Restarting

**Symptom**: Service restarts frequently, hits restart limit.

**Check:**
```bash
# View crash history
sudo journalctl -u trading-bot --since "1 hour ago" | grep "Started\|Stopped"

# Check for crash recovery events
curl http://localhost:8000/api/events?event_type=RECOVERY
```

**Solutions:**

1. **Review Error Logs**
   ```bash
   tail -100 /var/log/trading-bot/error.log
   ```

2. **Check System Resources**
   ```bash
   # Memory usage
   free -h

   # Disk space
   df -h

   # CPU usage
   top
   ```

3. **Reset Restart Counter**
   ```bash
   sudo systemctl reset-failed trading-bot
   sudo systemctl start trading-bot
   ```

### Service Stops Unexpectedly

**Check:**
```bash
# Check for OOM (Out of Memory) kills
sudo dmesg | grep -i "trading-bot\|python"

# View crash logs
sudo journalctl -u trading-bot --since "1 hour ago"
```

**Solutions:**

1. **Increase Memory Limit**
   Edit `/etc/systemd/system/trading-bot.service`:
   ```ini
   [Service]
   MemoryMax=4G  # Increase from 2G
   ```

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart trading-bot
   ```

2. **Check for Memory Leaks**
   ```bash
   curl http://localhost:8000/api/health/detailed | jq '.metrics.process.memory_mb'
   ```

## Connection Problems

### Cannot Connect to Database

**Symptom**: Error messages about database connection failures.

**Check:**
```bash
# Test database connection
curl http://localhost:8000/api/health/database

# Manual test
psql -U trading_user -d trading_db -c "SELECT 1"
```

**Solutions:**

1. **Verify PostgreSQL is Running**
   ```bash
   sudo systemctl status postgresql
   sudo systemctl start postgresql
   ```

2. **Check Connection String**
   Verify in `.env`:
   ```bash
   DATABASE_URL=postgresql://trading_user:password@localhost:5432/trading_db
   ```

3. **Check PostgreSQL Configuration**
   ```bash
   # Check if PostgreSQL accepts connections
   sudo -u postgres psql -c "SHOW listen_addresses;"

   # Should show localhost or *
   ```

4. **Verify Database Exists**
   ```bash
   sudo -u postgres psql -l | grep trading_db
   ```

### Cannot Connect to IBKR

**Symptom**: Broker health check fails, trades not executing.

**Check:**
```bash
# Test broker connection
curl http://localhost:8000/api/health/broker
```

**Solutions:**

1. **Verify TWS/Gateway is Running**
   - Check if TWS or IB Gateway window is open
   - Look for "Ready" status in TWS

2. **Check API Settings in TWS**
   - File > Global Configuration > API > Settings
   - ✅ Enable ActiveX and Socket Clients
   - ✅ Read-Only API: OFF
   - ✅ Port: 7497 (paper) or 7496 (live)
   - ✅ Trusted IPs: 127.0.0.1

3. **Verify Port in .env**
   ```bash
   grep IBKR_PORT /opt/trading-bot/.env
   # Should match TWS port
   ```

4. **Check Firewall**
   ```bash
   sudo ufw status
   # Ensure IBKR port is allowed
   sudo ufw allow 7497
   ```

5. **Test Manual Connection**
   ```bash
   telnet localhost 7497
   # Should connect without error
   ```

### WebSocket Connection Issues

**Symptom**: Dashboard doesn't update in real-time.

**Check Browser Console:**
```javascript
// In browser console (F12)
// Look for WebSocket connection errors
```

**Solutions:**

1. **Verify WebSocket Endpoint**
   Test in browser:
   ```javascript
   const ws = new WebSocket('ws://localhost:8000/ws/prices');
   ws.onopen = () => console.log('Connected');
   ws.onerror = (e) => console.error('Error:', e);
   ```

2. **Check CORS Settings**
   Verify in `.env`:
   ```bash
   BACKEND_CORS_ORIGINS=["http://localhost:3000"]
   ```

3. **Restart Service**
   ```bash
   sudo systemctl restart trading-bot
   ```

## Trading Issues

### Trades Not Executing

**Symptom**: Signals generated but no trades executed.

**Check:**
```bash
# View recent signals
curl http://localhost:8000/api/signals?hours=24

# View recent events
curl "http://localhost:8000/api/events?event_type=RISK&hours=24"
```

**Common Reasons:**

1. **Risk Rules Rejection**
   Check logs for:
   - "Daily loss limit exceeded"
   - "Position limit reached"
   - "Insufficient cash"
   - "Concentration limit exceeded"

2. **Strategy Not Active**
   ```bash
   curl http://localhost:8000/api/strategies
   # Check if status is "ACTIVE"
   ```

3. **No Cash Available**
   ```bash
   # Check account balance in TWS
   # Or query via API
   ```

4. **IBKR Connection Lost**
   ```bash
   curl http://localhost:8000/api/health/broker
   ```

**Solutions:**

1. **Review Risk Parameters**
   Adjust strategy risk settings:
   - Increase daily loss limit
   - Increase position limit
   - Reduce position size

2. **Activate Strategy**
   ```bash
   curl -X PUT http://localhost:8000/api/strategies/1/activate
   ```

3. **Add Funds**
   Deposit more cash into IBKR account

### Signals Not Generating

**Symptom**: No BUY/SELL signals appearing.

**Check:**
```bash
# View recent signals
curl http://localhost:8000/api/signals

# Check if data is being fetched
curl http://localhost:8000/api/stocks
```

**Solutions:**

1. **Verify Market Data**
   ```bash
   # Check if stock data exists
   curl "http://localhost:8000/api/market-data/AAPL?days=30"
   ```

2. **Check Twelve Data API Key**
   ```bash
   grep TWELVE_DATA_API_KEY /opt/trading-bot/.env

   # Test API key
   curl "https://api.twelvedata.com/time_series?symbol=AAPL&interval=1day&apikey=YOUR_KEY"
   ```

3. **Verify Scheduler is Running**
   ```bash
   curl http://localhost:8000/api/health/scheduler
   ```

4. **Check Strategy Configuration**
   Ensure MACD/RSI parameters are configured correctly.

### Incorrect Position Reconciliation

**Symptom**: Position reconciliation shows discrepancies after restart.

**Check:**
```bash
# View recovery events
curl http://localhost:8000/api/events?event_type=RECOVERY

# Check trades vs IBKR positions
```

**Solutions:**

1. **Review Recovery Report Email**
   Check your email for the recovery report sent on startup.

2. **Manual Reconciliation**
   ```bash
   # Compare database positions with TWS
   curl http://localhost:8000/api/trades?status=OPEN
   # vs positions shown in TWS
   ```

3. **Force Re-sync**
   Restart the application:
   ```bash
   sudo systemctl restart trading-bot
   ```

## Performance Issues

### Slow API Responses

**Symptom**: API calls take >5 seconds.

**Check:**
```bash
# Test response time
time curl http://localhost:8000/api/health

# Check system metrics
curl http://localhost:8000/api/health/detailed
```

**Solutions:**

1. **Check Database Performance**
   ```bash
   # Check active connections
   sudo -u postgres psql -d trading_db -c "SELECT count(*) FROM pg_stat_activity;"

   # Check slow queries
   sudo -u postgres psql -d trading_db -c "SELECT query, calls, total_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
   ```

2. **Optimize Database**
   ```bash
   # Vacuum database
   sudo -u postgres psql -d trading_db -c "VACUUM ANALYZE;"

   # Reindex
   sudo -u postgres psql -d trading_db -c "REINDEX DATABASE trading_db;"
   ```

3. **Check System Resources**
   ```bash
   # CPU usage
   top

   # Memory usage
   free -h

   # Disk I/O
   iostat
   ```

### High Memory Usage

**Symptom**: Application using >2GB memory.

**Check:**
```bash
curl http://localhost:8000/api/health/detailed | jq '.metrics.process.memory_mb'
```

**Solutions:**

1. **Restart Service**
   ```bash
   sudo systemctl restart trading-bot
   ```

2. **Check for Memory Leaks**
   Monitor memory over time:
   ```bash
   watch -n 60 'curl -s http://localhost:8000/api/health/detailed | jq ".metrics.process.memory_mb"'
   ```

3. **Reduce Data Retention**
   Clean old data:
   ```bash
   # Delete old market data
   psql -U trading_user -d trading_db -c "DELETE FROM stock_data WHERE timestamp < NOW() - INTERVAL '90 days';"
   ```

### Dashboard Not Loading

**Symptom**: Frontend shows errors or blank page.

**Check:**
```bash
# Check if frontend build exists
ls -la /opt/trading-bot/frontend/build/

# Check browser console for errors (F12)
```

**Solutions:**

1. **Rebuild Frontend**
   ```bash
   cd /opt/trading-bot/frontend
   npm run build
   ```

2. **Check Backend API**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Clear Browser Cache**
   - Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
   - Or clear browser cache completely

## Email Issues

### Not Receiving Emails

**Symptom**: Trade notifications or daily summaries not arriving.

**Check:**
```bash
# Check email settings
grep SMTP /opt/trading-bot/.env

# View application logs for email errors
grep -i "email\|smtp" /var/log/trading-bot/error.log
```

**Solutions:**

1. **Verify SMTP Settings**
   Test SMTP connection:
   ```bash
   python3 << EOF
   import smtplib
   from email.mime.text import MIMEText

   msg = MIMEText("Test")
   msg["Subject"] = "Test"
   msg["From"] = "your_email@gmail.com"
   msg["To"] = "your_email@gmail.com"

   with smtplib.SMTP("smtp.gmail.com", 587) as server:
       server.starttls()
       server.login("your_email@gmail.com", "your_app_password")
       server.send_message(msg)
   print("Email sent successfully")
   EOF
   ```

2. **Check Spam Folder**
   Emails might be filtered as spam.

3. **Verify Gmail App Password**
   - Go to Google Account > Security > 2-Step Verification > App passwords
   - Generate new app password if needed

4. **Check Email Quota**
   Gmail has sending limits (500 emails/day).

### Daily Summary Not Sent

**Symptom**: Daily summary email not arriving at 4:30 PM ET.

**Check:**
```bash
# Check if scheduler is running
curl http://localhost:8000/api/health/scheduler

# View scheduler logs
grep "Daily summary" /var/log/trading-bot/app.log
```

**Solutions:**

1. **Verify Scheduler Job**
   Check if daily_summary job is scheduled:
   ```bash
   curl http://localhost:8000/api/health/scheduler | jq '.jobs'
   ```

2. **Manually Trigger**
   ```bash
   # Trigger manually for testing
   python3 << EOF
   from app.db.session import SessionLocal
   from app.services.notifications.daily_summary import DailySummaryService

   db = SessionLocal()
   service = DailySummaryService(db)
   service.send_daily_summary()
   db.close()
   EOF
   ```

3. **Check Timezone**
   Ensure system timezone is correct:
   ```bash
   timedatectl
   # Should show America/New_York or adjust accordingly
   ```

## Data Issues

### Missing Market Data

**Symptom**: Indicators not calculated, signals not generated.

**Check:**
```bash
# Check if data exists
curl "http://localhost:8000/api/market-data/AAPL?days=30"

# Check data update logs
grep "Daily bar update" /var/log/trading-bot/app.log
```

**Solutions:**

1. **Verify API Key**
   Test Twelve Data API:
   ```bash
   curl "https://api.twelvedata.com/time_series?symbol=AAPL&interval=1day&outputsize=30&apikey=YOUR_KEY"
   ```

2. **Manually Fetch Data**
   ```bash
   # Trigger data update
   curl -X POST "http://localhost:8000/api/scheduler/run-daily-update"
   ```

3. **Check API Quota**
   Twelve Data free tier has limits (800 API calls/day).

### Indicators Not Updating

**Symptom**: MACD/RSI values are stale or missing.

**Check:**
```bash
# Check indicator data
curl "http://localhost:8000/api/indicators/AAPL?days=30"
```

**Solutions:**

1. **Recalculate Indicators**
   ```bash
   # Re-run indicator calculation
   python3 << EOF
   from app.db.session import SessionLocal
   from app.services.indicators.indicator_service import IndicatorService

   db = SessionLocal()
   service = IndicatorService(db)
   service.calculate_indicators("AAPL")
   db.close()
   EOF
   ```

2. **Check Data Pipeline**
   Verify data flows: Market Data → Indicators → Signals → Trades

## Error Messages

### "Failed to connect to database"

**Cause**: PostgreSQL not running or connection refused.

**Solution:**
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### "IBKR connection timeout"

**Cause**: TWS/Gateway not running or API disabled.

**Solution:**
1. Start TWS/IB Gateway
2. Enable API in TWS settings
3. Verify port matches .env configuration

### "Insufficient cash for trade"

**Cause**: Not enough available cash in account.

**Solution:**
1. Deposit more funds to IBKR account
2. Reduce position size in strategy config
3. Wait for existing positions to close

### "Daily loss limit exceeded"

**Cause**: Today's losses reached configured limit.

**Solution:**
1. Wait until next trading day
2. Increase daily loss limit (if appropriate)
3. Review and adjust strategy

### "API rate limit exceeded"

**Cause**: Too many API calls to Twelve Data.

**Solution:**
1. Upgrade Twelve Data plan
2. Reduce polling frequency
3. Wait for quota to reset (usually 24 hours)

## FAQ

### Q: How do I reset the system completely?

**A:**
```bash
# Stop service
sudo systemctl stop trading-bot

# Backup database
sudo -u postgres pg_dump trading_db > /tmp/backup.sql

# Drop and recreate database
sudo -u postgres psql -c "DROP DATABASE trading_db;"
sudo -u postgres psql -c "CREATE DATABASE trading_db OWNER trading_user;"

# Run migrations
cd /opt/trading-bot/backend
source venv/bin/activate
alembic upgrade head

# Start service
sudo systemctl start trading-bot
```

### Q: Can I run multiple strategies simultaneously?

**A:** Yes, create multiple strategy records with different configurations. Each can trade different stocks or use different parameters.

### Q: How do I switch from paper to live trading?

**A:**
```bash
# 1. Update .env
nano /opt/trading-bot/.env
# Change IBKR_TRADING_MODE=live
# Change IBKR_PORT=7496

# 2. Restart TWS in live mode

# 3. Restart service
sudo systemctl restart trading-bot

# ⚠️ WARNING: Double-check all settings before enabling live trading!
```

### Q: Where are the log files located?

**A:**
- Application logs: `/var/log/trading-bot/app.log`
- Error logs: `/var/log/trading-bot/error.log`
- systemd logs: `journalctl -u trading-bot`

### Q: How do I view all trades for a specific symbol?

**A:**
```bash
curl "http://localhost:8000/api/trades?symbol=AAPL"
```

### Q: Can I backtest multiple symbols at once?

**A:** Currently, backtests run one symbol at a time. Run separate backtests for each symbol and compare results.

### Q: How often does the system check for signals?

**A:** Market data is fetched every 30 seconds during market hours. Signals are generated immediately after indicator calculations.

### Q: What happens if I lose internet connection?

**A:** The system will:
1. Log connection errors
2. Attempt to reconnect automatically
3. Send error notification email
4. Run recovery procedure on reconnection
5. Reconcile positions with broker

### Q: Can I modify the MACD/RSI parameters?

**A:** Yes, update strategy configuration through the API or database. Changes take effect immediately for new signals.

## Getting Additional Help

If you've tried the solutions above and still have issues:

1. **Check Documentation**
   - Review `docs/DEPLOYMENT.md`
   - Review `docs/USER_MANUAL.md`

2. **Collect Diagnostic Info**
   ```bash
   # System info
   uname -a
   free -h
   df -h

   # Service status
   sudo systemctl status trading-bot

   # Recent logs
   sudo journalctl -u trading-bot -n 100 --no-pager

   # Health check
   curl http://localhost:8000/api/health/detailed
   ```

3. **Contact Support**
   - GitHub Issues: https://github.com/yourusername/trading-bot/issues
   - Email: support@yourdomain.com
   - Include diagnostic info from step 2

## Emergency Procedures

### Stop All Trading Immediately

```bash
# Method 1: Pause all strategies
curl -X PUT http://localhost:8000/api/strategies/1/pause

# Method 2: Stop service
sudo systemctl stop trading-bot

# Method 3: Close all positions manually in TWS
```

### Restore from Backup

```bash
# Stop service
sudo systemctl stop trading-bot

# Restore database
gunzip -c /var/backups/trading-bot/backup_YYYYMMDD.sql.gz | sudo -u postgres psql trading_db

# Start service
sudo systemctl start trading-bot
```

### Factory Reset

```bash
# Complete reset (⚠️ DESTROYS ALL DATA)
sudo systemctl stop trading-bot
sudo -u postgres psql -c "DROP DATABASE trading_db;"
sudo -u postgres psql -c "CREATE DATABASE trading_db OWNER trading_user;"
cd /opt/trading-bot/backend
source venv/bin/activate
alembic upgrade head
sudo systemctl start trading-bot
```
