# Claude Code Observability Tools - Setup and Integration Guide

This guide explains how to set up and integrate the Python-based observability logging and reporting tools with your Claude Code deployment.

## 🏗️ Architecture Overview

The observability tools complement the existing OpenTelemetry/Prometheus/Grafana stack by adding:

- **Background Logger**: Parses observability data and stores it in SQLite
- **Report Generator**: Creates detailed historical reports (CSV, PDF, JSON)
- **Database Schema**: Normalized storage optimized for analytics

```
Claude Code → OpenTelemetry → [Prometheus/Loki] → Grafana (Real-time)
                           ↘
                            Background Logger → SQLite → Reports (Historical)
```

## 📋 Prerequisites

- Python 3.8+ installed
- Claude Code configured with OpenTelemetry telemetry
- Running Claude Code Observability Stack (optional, for real-time monitoring)

## 🚀 Quick Setup

### 1. Install Dependencies

```bash
# Install Python dependencies
make install-observability-tools

# Or manually:
pip install -r tools/requirements.txt
```

### 2. Configure Claude Code Telemetry

Ensure Claude Code is configured to export telemetry data:

```bash
# Enable telemetry
export CLAUDE_CODE_ENABLE_TELEMETRY=1

# Configure OTLP exporters
export OTEL_METRICS_EXPORTER=otlp
export OTEL_LOGS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# Optional: Faster export for testing
export OTEL_METRIC_EXPORT_INTERVAL=10000
export OTEL_LOGS_EXPORT_INTERVAL=5000
```

### 3. Start Background Logger

Choose the appropriate method based on your setup:

#### Option A: With Docker Stack (Recommended)

```bash
# Start the observability stack first
make up

# Start background logger reading from collector
make start-logger
```

#### Option B: Log File Input

```bash
# Direct Claude Code output to a log file
claude > /tmp/claude_code.log 2>&1 &

# Start logger reading from file
make start-logger-file LOG_FILE=/tmp/claude_code.log
```

#### Option C: Stdin Input

```bash
# Pipe Claude Code output directly to logger
claude 2>&1 | make start-logger-stdin
```

### 4. Generate Reports

```bash
# Weekly reports
make generate-cost-report
make generate-user-report

# Monthly reports
make generate-monthly-reports

# Custom period
make generate-custom-report START_DATE=2024-01-01 END_DATE=2024-01-31 REPORT_TYPE=cost
```

## 🔧 Configuration Options

### Environment Variables

Set these in your shell or deployment configuration:

```bash
# Database location
export CLAUDE_CODE_DB_PATH="/path/to/claude_code_observability.db"

# Logging level
export CLAUDE_CODE_LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR

# Reports output directory
export CLAUDE_CODE_REPORTS_DIR="/path/to/reports"
```

### Background Logger Configuration

The background logger supports multiple configuration options:

```bash
cd tools/logger
python background_logger.py \
  --source /var/log/claude_code.log \
  --source-type file \
  --db-path /path/to/database.db \
  --log-level INFO
```

#### Source Types:
- `file`: Read from log file with tailing
- `docker`: Read from Docker container logs
- `stdin`: Read from standard input

### Report Generator Configuration

```bash
cd tools/reports
python generate_reports.py \
  --report-type cost \
  --period month \
  --format csv --format pdf \
  --output-dir /path/to/reports \
  --db-path /path/to/database.db
```

## 🏭 Production Deployment

### Systemd Service (Linux)

Create `/etc/systemd/system/claude-observability-logger.service`:

```ini
[Unit]
Description=Claude Code Observability Background Logger
After=network.target

[Service]
Type=simple
User=claude-user
WorkingDirectory=/opt/claude-code-otel/tools/logger
ExecStart=/usr/bin/python3 background_logger.py --source otel-collector --source-type docker --db-path /var/lib/claude-observability/database.db
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable claude-observability-logger
sudo systemctl start claude-observability-logger
```

### Docker Container

Create a Dockerfile for the logger:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY tools/logger/ /app/logger/
COPY tools/requirements.txt /app/

RUN pip install -r requirements.txt

CMD ["python", "logger/background_logger.py", "--source", "otel-collector", "--source-type", "docker"]
```

Add to docker-compose.yml:
```yaml
services:
  claude-observability-logger:
    build: .
    volumes:
      - ./data:/app/data
    depends_on:
      - otel-collector
    restart: unless-stopped
```

### Cron Jobs for Reports

Add to crontab for automated report generation:

```bash
# Daily cost reports at 8 AM
0 8 * * * cd /opt/claude-code-otel && make generate-cost-report

# Weekly user activity reports (Mondays at 9 AM)
0 9 * * 1 cd /opt/claude-code-otel && make generate-user-report

# Monthly comprehensive reports (1st of month at 10 AM)
0 10 1 * * cd /opt/claude-code-otel && make generate-monthly-reports
```

## 🔍 Integration Patterns

### 1. Standalone Deployment

Use only the SQLite-based tools without the full observability stack:

```bash
# Start logger reading from Claude Code directly
claude 2>&1 | python tools/logger/background_logger.py --source stdin --source-type stdin

# Generate reports as needed
python tools/reports/generate_reports.py --report-type cost --period week --format csv
```

### 2. Hybrid Deployment

Use both real-time dashboards and historical reporting:

- **Grafana**: Real-time monitoring and alerting
- **SQLite Tools**: Historical analysis and detailed reporting

### 3. Multi-Instance Deployment

For multiple Claude Code deployments:

1. Run separate logger instances with different database files
2. Aggregate data using custom SQL queries
3. Generate consolidated reports

```bash
# Instance 1
python background_logger.py --db-path team1_observability.db --source team1-logs

# Instance 2  
python background_logger.py --db-path team2_observability.db --source team2-logs

# Consolidated reporting (custom script)
sqlite3 consolidated.db "ATTACH 'team1_observability.db' AS team1; ATTACH 'team2_observability.db' AS team2; ..."
```

## 📊 Data Schema and Queries

### Database Tables

The SQLite database contains:

- **sessions**: Session metadata and user information
- **metrics**: Time-series metrics data  
- **events**: Structured event logs
- **costs**: Denormalized cost data for reporting
- **user_activity**: Denormalized user activity for analytics

### Common Queries

```sql
-- Top users by cost (last 30 days)
SELECT 
    user_account_uuid,
    SUM(cost_usd) as total_cost,
    COUNT(*) as sessions
FROM costs 
WHERE timestamp > datetime('now', '-30 days')
GROUP BY user_account_uuid 
ORDER BY total_cost DESC;

-- Daily session trends
SELECT 
    DATE(start_time) as date,
    COUNT(*) as sessions,
    COUNT(DISTINCT user_account_uuid) as unique_users
FROM sessions 
WHERE start_time > datetime('now', '-30 days')
GROUP BY DATE(start_time) 
ORDER BY date;

-- Model usage breakdown
SELECT 
    model,
    COUNT(*) as requests,
    SUM(cost_usd) as total_cost,
    AVG(cost_usd) as avg_cost_per_request
FROM costs 
GROUP BY model 
ORDER BY total_cost DESC;
```

## 🔧 Troubleshooting

### Common Issues

**1. No data being collected**
- Check Claude Code telemetry configuration
- Verify OpenTelemetry collector is running
- Enable debug logging: `--log-level DEBUG`

**2. Database permission errors**
- Ensure write permissions for database directory
- Check file ownership and group permissions

**3. Report generation fails**
- Verify database has data: `make check-db`
- Check available disk space for reports
- Install optional dependencies: `pip install reportlab`

**4. Background logger stops**
- Check system logs for errors
- Verify log source is still available
- Restart with systemd or Docker

### Debug Mode

Enable detailed logging to troubleshoot parsing issues:

```bash
python tools/logger/background_logger.py \
  --source /path/to/logs \
  --source-type file \
  --log-level DEBUG
```

### Database Maintenance

```bash
# Check database size and table counts
make check-db

# Clean old data (older than 90 days)
sqlite3 claude_code_observability.db "DELETE FROM metrics WHERE timestamp < datetime('now', '-90 days');"

# Vacuum database to reclaim space
sqlite3 claude_code_observability.db "VACUUM;"

# Reset database completely
make clean-db
```

## 📈 Performance Considerations

### Database Performance

- The database is indexed for common query patterns
- For high-volume deployments, consider periodic cleanup of old data
- SQLite can handle ~100K writes/second for this workload

### Memory Usage

- Background logger: ~10-50MB RAM
- Report generation: ~50-200MB RAM (depending on data volume)

### Disk Usage

- Database grows ~1MB per 10K metrics
- Reports are typically 1-10MB each
- Log rotation recommended for long-running deployments

## 🔒 Security Considerations

### Data Privacy

- User prompt content is redacted by default
- Set `OTEL_LOG_USER_PROMPTS=1` only if needed
- Database contains usage metadata, not source code

### Access Control

- Secure database file permissions (600 or 640)
- Limit access to reports directory
- Use HTTPS for any web-based report distribution

### Network Security

- Logger connects to local OpenTelemetry collector only
- No external network access required
- Consider firewall rules for Docker deployments

## 📚 Advanced Usage

### Custom Metrics

Add custom metrics by extending the parsing patterns in `background_logger.py`:

```python
self.metric_patterns['custom_metric'] = re.compile(r'my_app\.custom_metric.*?value:\s*(\d+\.?\d*)')
```

### Report Customization

Extend the report generator for custom report types:

```python
def generate_custom_report(self, period: str):
    # Custom query logic
    # Custom report formatting
    pass
```

### Data Export

Export data to other systems:

```python
# Export to ClickHouse, BigQuery, etc.
import pandas as pd
df = pd.read_sql_query("SELECT * FROM metrics", sqlite3.connect("database.db"))
```

## 🤝 Support and Contributing

### Getting Help

1. Check the troubleshooting section above
2. Review the tools/README.md for detailed API documentation
3. Enable debug logging to diagnose parsing issues

### Contributing

To add new features:

1. Update database schema in `database.py`
2. Add parsing logic in `background_logger.py`
3. Extend report generation in `generate_reports.py`
4. Add tests in `test_observability.py`
5. Update documentation

### Testing Changes

```bash
# Run the test suite
make test-observability

# Test specific components
cd tools
python test_observability.py
python logger/background_logger.py --help
python reports/generate_reports.py --help
```