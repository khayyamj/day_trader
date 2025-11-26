# Phase 7: System Operations & Monitoring (Weeks 13-14)

## PRD Reference

**Source:** `/PRD.md`
**Key Requirements:**
- Implement email notification service for trade execution, alerts, daily summaries
- Build comprehensive event logging system for audit trail
- Create crash recovery procedure with position reconciliation
- Set up systemd service for automatic restart (max 5 restarts in 10 minutes)
- Implement daily summary email at market close (4:30 PM ET)
- Create system health monitoring endpoints
- Run comprehensive integration tests across all components
- Perform load and stress testing
- Fix critical bugs identified during testing
- Complete deployment documentation and user manual

**Development Approach:** Implementation-first with manual testing, automated tests and documentation at end of cycle

## Relevant Files

### To Be Created:
- `backend/app/services/notifications/` - Notification services directory
- `backend/app/services/notifications/email_service.py` - SMTP email sender
- `backend/app/services/notifications/notification_manager.py` - Notification coordinator
- `backend/app/services/notifications/templates/` - Email templates directory
- `backend/app/services/notifications/templates/trade_execution.html` - Trade notification template
- `backend/app/services/notifications/templates/daily_summary.html` - Daily summary template
- `backend/app/services/notifications/templates/alert.html` - Alert notification template
- `backend/app/services/monitoring/` - Monitoring services directory
- `backend/app/services/monitoring/health_check.py` - System health checker
- `backend/app/services/monitoring/recovery.py` - Crash recovery service
- `backend/app/api/endpoints/health.py` - Health check endpoints
- `backend/app/api/endpoints/admin.py` - Admin endpoints (restart, status)
- `deploy/` - Deployment files directory
- `deploy/trading-bot.service` - systemd service file
- `deploy/setup.sh` - Deployment setup script
- `tests/integration/` - Integration tests directory
- `tests/load/` - Load testing scripts
- `docs/DEPLOYMENT.md` - Deployment guide
- `docs/USER_MANUAL.md` - User manual
- `docs/TROUBLESHOOTING.md` - Troubleshooting guide

### Files to Modify:
- `backend/app/main.py` - Add health check routes, startup/shutdown events
- `backend/app/core/config.py` - Add SMTP settings
- `backend/app/services/data/scheduler.py` - Add daily summary job
- `.env.example` - Add email settings

### Notes

- Focus on implementing reliable operations that can be monitored
- Test all failure scenarios: email failures, crashes, API outages
- Verify systemd service restarts app correctly after crashes
- Test daily summary email by manually triggering
- Comprehensive integration tests are critical for Phase 7
- Bug fixing and polishing takes priority in Week 14

## Tasks

| Task |  #  | Status | Description                               |     | Dependencies | Pts | Time Spent |
| :--: | :-: | :----: | ----------------------------------------- | :-: | :----------: | :-: | :--------: |
|  1   |     |   ✅   | **Implement Email Notification Service**  | 🟢  |      -       |  -  |   2h 30m   |
|      |  1  |   ✅   | Add SMTP settings to .env: SMTP_HOST,     | 🟢  |      -       |  1  |    10m     |
|      |     |        | SMTP_PORT, SMTP_USER, SMTP_PASSWORD,      |     |              |     |            |
|      |     |        | EMAIL_FROM                                |     |              |     |            |
|      |  2  |   ✅   | Create                                    | 🟢  |      -       |  5  |    20m     |
|      |     |        | services/notifications/email_service.py   |     |              |     |            |
|      |     |        | with EmailService class using             |     |              |     |            |
|      |     |        | smtplib                                   |     |              |     |            |
|      |  3  |   ✅   | Implement send_email() method with HTML   | 🟢  |      -       |  3  |    15m     |
|      |     |        | and plain text support                    |     |              |     |            |
|      |  4  |   ✅   | Add retry logic for email sending (3      | 🟢  |      -       |  2  |    10m     |
|      |     |        | attempts, 5 second delay)                 |     |              |     |            |
|      |  5  |   ✅   | Create HTML email templates using Jinja2  | 🟢  |      -       |  3  |    15m     |
|      |     |        | for trade_execution.html                  |     |              |     |            |
|      |  6  |   ✅   | Create templates for alert.html and       | 🟢  |      -       |  3  |    25m     |
|      |     |        | daily_summary.html                        |     |              |     |            |
|      |  7  |   ✅   | Test email sending: send test email to    | 🟢  |      -       |  1  |     5m     |
|      |     |        | your address, verify received             |     |              |     |            |
|      |  8  |   ✅   | Create                                    | 🟢  |      -       |  5  |    20m     |
|      |     |        | services/notifications/notification_manager.py |   |              |     |            |
|      |     |        | that coordinates all notifications        |     |              |     |            |
|      |  9  |   ✅   | Implement notify_trade_execution() that   | 🟢  |      -       |  3  |    10m     |
|      |     |        | sends email on trade entry/exit           |     |              |     |            |
|      | 10  |   ✅   | Implement notify_risk_warning() for       | 🟢  |      -       |  2  |    10m     |
|      |     |        | daily loss limit warnings                 |     |              |     |            |
|      | 11  |   ✅   | Implement notify_system_error() for       | 🟢  |      -       |  2  |    10m     |
|      |     |        | critical errors and crashes               |     |              |     |            |
|  2   |     |   ✅   | **Build Event Logging System**            | 🟢  |      -       |  -  |   1h 45m   |
|      |  1  |   ✅   | Enhance existing logging to include       | 🟢  |      -       |  3  |    20m     |
|      |     |        | structured logging (JSON format)          |     |              |     |            |
|      |  2  |   ✅   | Add context logging: include trade_id,    | 🟢  |      -       |  3  |    15m     |
|      |     |        | strategy_id, user_id in all log           |     |              |     |            |
|      |     |        | entries                                   |     |              |     |            |
|      |  3  |   ✅   | Implement database logging for critical   | 🟢  |      -       |  3  |    20m     |
|      |     |        | events: save to strategy_events table     |     |              |     |            |
|      |  4  |   ✅   | Create log_event() helper that logs both  | 🟢  |      -       |  2  |    15m     |
|      |     |        | to file and database                      |     |              |     |            |
|      |  5  |   ✅   | Add event logging throughout application: | 🟢  |      -       |  5  |    20m     |
|      |     |        | trade execution, signal generation,       |     |              |     |            |
|      |     |        | order placement, risk rejections          |     |              |     |            |
|      |  6  |   ✅   | Implement log rotation and archival:      | 🟢  |      -       |  2  |     5m     |
|      |     |        | keep 30 days hot, 90 days cold            |     |              |     |            |
|      |  7  |   ✅   | Create GET /api/events endpoint to query  | 🟢  |      -       |  3  |    15m     |
|      |     |        | recent events with filters                |     |              |     |            |
|      |  8  |   ✅   | Test event logging: trigger various       | 🟢  |      -       |  2  |     5m     |
|      |     |        | scenarios, verify events logged           |     |              |     |            |
|  3   |     |   ✅   | **Create Crash Recovery Procedure**       | 🟢  |      -       |  -  |   2h 15m   |
|      |  1  |   ✅   | Create services/monitoring/recovery.py    | 🟢  |      -       |  5  |    30m     |
|      |     |        | with RecoveryService class                |     |              |     |            |
|      |  2  |   ✅   | Implement detect_crash() that checks if   | 🟢  |      -       |  3  |    15m     |
|      |     |        | system_state.last_updated > 5 minutes     |     |              |     |            |
|      |     |        | ago                                       |     |              |     |            |
|      |  3  |   ✅   | Implement run_recovery() method that      | 🟢  |      -       |  5  |    30m     |
|      |     |        | loads last state, reconciles with         |     |              |     |            |
|      |     |        | broker, logs recovery event               |     |              |     |            |
|      |  4  |   ✅   | Add system_state table with               | 🟢  |      -       |  2  |    10m     |
|      |     |        | last_updated, system_status,              |     |              |     |            |
|      |     |        | metadata fields                           |     |              |     |            |
|      |  5  |   ✅   | Add recovery_events table to log all      | 🟢  |      -       |  2  |    10m     |
|      |     |        | recovery attempts and outcomes            |     |              |     |            |
|      |  6  |   ✅   | Update system_state.last_updated every    | 🟢  |      -       |  2  |    15m     |
|      |     |        | 30 seconds via heartbeat                  |     |              |     |            |
|      |  7  |   ✅   | Run recovery on app startup               | 🟢  |      -       |  2  |    15m     |
|      |     |        | automatically                             |     |              |     |            |
|      |  8  |   ✅   | Send recovery report email with           | 🟢  |      -       |  3  |    10m     |
|      |     |        | discrepancies, actions taken,             |     |              |     |            |
|      |     |        | positions status                          |     |              |     |            |
|      |  9  |   ✅   | Test recovery: stop app during active     | 🟢  |      -       |  3  |    10m     |
|      |     |        | trade, restart, verify reconciliation     |     |              |     |            |
|  4   |     |   ✅   | **Set Up Auto-Restart Service            | 🟢  |      -       |  -  |   1h 0m    |
|      |     |        | (systemd)**                               |     |              |     |            |
|      |  1  |   ✅   | Create deploy/trading-bot.service file    | 🟢  |      -       |  3  |    15m     |
|      |     |        | with Restart=always, RestartSec=10s       |     |              |     |            |
|      |  2  |   ✅   | Add restart limits: StartLimitInterval=   | 🟢  |      -       |  2  |     5m     |
|      |     |        | 600, StartLimitBurst=5 (max 5             |     |              |     |            |
|      |     |        | restarts in 10 min)                       |     |              |     |            |
|      |  3  |   ✅   | Configure log output: StandardOutput and  | 🟢  |      -       |  1  |     5m     |
|      |     |        | StandardError to log files                |     |              |     |            |
|      |  4  |   ✅   | Add dependencies: After=network.target    | 🟢  |      -       |  1  |     5m     |
|      |     |        | postgresql.service                        |     |              |     |            |
|      |  5  |   ✅   | Create deploy/setup.sh script to install  | 🟢  |      -       |  3  |    20m     |
|      |     |        | service: copy to /etc/systemd/system,     |     |              |     |            |
|      |     |        | enable, start                             |     |              |     |            |
|      |  6  |   ✅   | Test systemd service: enable, start,      | 🟢  |      -       |  2  |     5m     |
|      |     |        | verify running with systemctl status      |     |              |     |            |
|      |  7  |   ✅   | Test auto-restart: kill process, verify   | 🟢  |      -       |  2  |     5m     |
|      |     |        | systemd restarts it within 10 seconds     |     |              |     |            |
|      |  8  |   ✅   | Test restart limits: cause 6 rapid        | 🟢  |      -       |  2  |     5m     |
|      |     |        | crashes, verify service stops after       |     |              |     |            |
|      |     |        | 5th                                       |     |              |     |            |
|  5   |     |   ✅   | **Implement Daily Summary Email**         | 🟢  |      -       |  -  |   1h 30m   |
|      |  1  |   ✅   | Create generate_daily_summary() method    | 🟢  |      1       |  5  |    30m     |
|      |     |        | that queries: trades today, P&L,          |     |              |     |            |
|      |     |        | win rate, open positions                  |     |              |     |            |
|      |  2  |   ✅   | Format summary data into HTML email       | 🟢  |      -       |  3  |    15m     |
|      |     |        | with tables and charts                    |     |              |     |            |
|      |  3  |   ✅   | Add daily_summary_job() to scheduler that | 🟢  |      -       |  3  |    20m     |
|      |     |        | runs at 4:30 PM ET (after market         |     |              |     |            |
|      |     |        | close)                                    |     |              |     |            |
|      |  4  |   ✅   | Send summary email to configured address  | 🟢  |      -       |  2  |    10m     |
|      |  5  |   ✅   | Add "Tomorrow's Watchlist" section        | 🟢  |      -       |  2  |    10m     |
|      |     |        | showing stocks near signals               |     |              |     |            |
|      |  6  |   ✅   | Test daily summary: manually trigger job, | 🟢  |      -       |  2  |     5m     |
|      |     |        | verify email received with correct        |     |              |     |            |
|      |     |        | data                                      |     |              |     |            |
|  6   |     |   ✅   | **Create System Health Monitoring**       | 🟢  |      -       |  -  |   1h 20m   |
|      |  1  |   ✅   | Create                                    | 🟢  |      -       |  5  |    25m     |
|      |     |        | services/monitoring/health_check.py       |     |              |     |            |
|      |     |        | with HealthChecker class                  |     |              |     |            |
|      |  2  |   ✅   | Implement check_database() that tests     | 🟢  |      -       |  2  |    10m     |
|      |     |        | DB connection and query                   |     |              |     |            |
|      |  3  |   ✅   | Implement check_broker_connection() that  | 🟢  |      -       |  2  |    10m     |
|      |     |        | tests IBKR API connection                 |     |              |     |            |
|      |  4  |   ✅   | Implement check_scheduler() that verifies | 🟢  |      -       |  2  |    10m     |
|      |     |        | scheduled jobs are running                |     |              |     |            |
|      |  5  |   ✅   | Implement check_disk_space() that warns   | 🟢  |      -       |  2  |    10m     |
|      |     |        | if < 1GB free                             |     |              |     |            |
|      |  6  |   ✅   | Create GET /api/health endpoint returning | 🟢  |      -       |  3  |    15m     |
|      |     |        | overall status and component checks       |     |              |     |            |
|      |  7  |   ✅   | Create GET /api/health/detailed with full | 🟢  |      -       |  2  |    10m     |
|      |     |        | system metrics                            |     |              |     |            |
|      |  8  |   ✅   | Test health checks: disconnect DB, stop   | 🟢  |      -       |  2  |     5m     |
|      |     |        | IBKR, verify endpoint reports issues      |     |              |     |            |
|  7   |     |   -    | **Run Comprehensive Integration Tests**   | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Create tests/integration/ directory for   | 🟢  |      -       |  2  |     -      |
|      |     |        | end-to-end tests                          |     |              |     |            |
|      |  2  |   -    | Create test_full_trading_flow.py: fetch   | 🟡  |     7.1      |  8  |     -      |
|      |     |        | data, calculate indicators, generate      |     |              |     |            |
|      |     |        | signal, execute trade, verify in DB       |     |              |     |            |
|      |  3  |   -    | Create test_backtesting_flow.py: run      | 🟡  |     7.1      |  5  |     -      |
|      |     |        | backtest, verify metrics calculated       |     |              |     |            |
|      |  4  |   -    | Create test_risk_management.py: test all  | 🟡  |     7.1      |  5  |     -      |
|      |     |        | risk rule rejections                      |     |              |     |            |
|      |  5  |   -    | Create test_crash_recovery.py: simulate   | 🟡  |     3, 7.1   |  5  |     -      |
|      |     |        | crash, verify recovery works              |     |              |     |            |
|      |  6  |   -    | Create test_notifications.py: trigger     | 🟡  |     1, 7.1   |  3  |     -      |
|      |     |        | events, verify emails sent                |     |              |     |            |
|      |  7  |   -    | Run all integration tests and fix any     | 🟡  |     7.2-7.6  |  5  |     -      |
|      |     |        | failures                                  |     |              |     |            |
|  8   |     |   -    | **Perform Load and Stress Testing**       | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Create tests/load/ directory for load     | 🟢  |      -       |  1  |     -      |
|      |     |        | tests                                     |     |              |     |            |
|      |  2  |   -    | Install locust or artillery for load      | 🟡  |     8.1      |  1  |     -      |
|      |     |        | testing                                   |     |              |     |            |
|      |  3  |   -    | Create load test for WebSocket            | 🟡  |     8.2      |  3  |     -      |
|      |     |        | connections: 10 concurrent clients        |     |              |     |            |
|      |  4  |   -    | Create load test for API endpoints: 100   | 🟡  |     8.2      |  3  |     -      |
|      |     |        | requests/second                           |     |              |     |            |
|      |  5  |   -    | Test with 10 watchlist stocks, verify     | 🟡  |     8.3-8.4  |  3  |     -      |
|      |     |        | system handles load                       |     |              |     |            |
|      |  6  |   -    | Measure response times: ensure dashboard  | 🟡  |     8.5      |  2  |     -      |
|      |     |        | loads <3s, API calls <500ms               |     |              |     |            |
|      |  7  |   -    | Identify and fix performance bottlenecks  | 🟡  |     8.6      |  5  |     -      |
|  9   |     |   -    | **Fix Critical Bugs**                     | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Create bug tracking document or use       | 🟢  |      7, 8    |  1  |     -      |
|      |     |        | GitHub issues                             |     |              |     |            |
|      |  2  |   -    | Prioritize bugs: Critical (blocks MVP),   | 🟡  |     9.1      |  2  |     -      |
|      |     |        | High (major impact), Medium, Low          |     |              |     |            |
|      |  3  |   -    | Fix all Critical bugs identified during   | 🟡  |     9.2      |  8  |     -      |
|      |     |        | testing                                   |     |              |     |            |
|      |  4  |   -    | Fix High priority bugs if time allows     | 🟡  |     9.3      |  5  |     -      |
|      |  5  |   -    | Regression test: re-run all tests after   | 🟡  |     9.3-9.4  |  3  |     -      |
|      |     |        | bug fixes                                 |     |              |     |            |
|      |  6  |   -    | Document known issues that won't be       | 🟡  |     9.5      |  2  |     -      |
|      |     |        | fixed in MVP                              |     |              |     |            |
| 10   |     |   ✅   | **Write Deployment Documentation**        | 🟢  |      -       |  -  |   1h 15m   |
|      |  1  |   ✅   | Create docs/DEPLOYMENT.md with complete   | 🟢  |      -       |  5  |    25m     |
|      |     |        | setup instructions                        |     |              |     |            |
|      |  2  |   ✅   | Document prerequisites: Python, Node,     | 🟢  |      -       |  2  |    15m     |
|      |     |        | PostgreSQL, Redis, IBKR account           |     |              |     |            |
|      |  3  |   ✅   | Document step-by-step deployment: clone,  | 🟢  |      -       |  3  |    15m     |
|      |     |        | install deps, configure .env, run         |     |              |     |            |
|      |     |        | migrations, start services                |     |              |     |            |
|      |  4  |   ✅   | Document systemd service setup and        | 🟢  |      -       |  2  |    10m     |
|      |     |        | management commands                       |     |              |     |            |
|      |  5  |   ✅   | Document monitoring: checking logs,       | 🟢  |      -       |  2  |    10m     |
|      |     |        | health endpoints, email alerts            |     |              |     |            |
|      |  6  |   ✅   | Document backup and restore procedures    | 🟢  |      -       |  2  |    10m     |
|      |     |        | for database                              |     |              |     |            |
| 11   |     |   ✅   | **Create User Manual and Troubleshooting  | 🟢  |      -       |  -  |   2h 0m    |
|      |     |        | Guide**                                   |     |              |     |            |
|      |  1  |   ✅   | Create docs/USER_MANUAL.md with           | 🟢  |      10      |  5  |    35m     |
|      |     |        | overview, features, getting started       |     |              |     |            |
|      |  2  |   ✅   | Document dashboard usage: understanding   | 🟢  |      -       |  3  |    15m     |
|      |     |        | charts, tables, indicators                |     |              |     |            |
|      |  3  |   ✅   | Document strategy configuration: how to   | 🟢  |      -       |  3  |    15m     |
|      |     |        | activate, pause, update parameters        |     |              |     |            |
|      |  4  |   ✅   | Document risk management: position        | 🟢  |      -       |  3  |    15m     |
|      |     |        | sizing, limits, loss limits               |     |              |     |            |
|      |  5  |   ✅   | Create docs/TROUBLESHOOTING.md with       | 🟢  |      -       |  5  |    30m     |
|      |     |        | common issues and solutions               |     |              |     |            |
|      |  6  |   ✅   | Document common errors: connection        | 🟢  |      -       |  3  |    10m     |
|      |     |        | failures, order rejections, data          |     |              |     |            |
|      |     |        | issues                                    |     |              |     |            |
|      |  7  |   ✅   | Add FAQ section with answers to common    | 🟢  |      -       |  2  |     5m     |
|      |     |        | questions                                 |     |              |     |            |
|      |  8  |   ✅   | Include contact/support information       | 🟢  |      -       |  1  |     5m     |

---

**Phase 7 Total Sprint Points:** ~191 points
**Estimated Duration:** 2 weeks
**Key Deliverables:** Email notification service working, comprehensive event logging, crash recovery tested, systemd auto-restart configured, daily summary emails, system health monitoring, all integration tests passing, load testing completed, critical bugs fixed, complete deployment documentation and user manual
