# Claude Code Observability Tools

This directory contains Python-based tools for logging observability metrics and events from Claude Code into a local SQLite database, and generating historical reports.

## 🏗️ Architecture

```
Claude Code (OTEL) → Background Logger → SQLite Database → Report Generator → CSV/PDF/JSON
                                      ↓
                              OpenTelemetry → Prometheus/Loki → Grafana (existing stack)
```

## 📦 Components

### 1. Background Logger (`tools/logger/`)
- **Purpose**: Continuously reads and parses log data from Claude Code for observability metrics
- **Input Sources**: 
  - OpenTelemetry collector Docker logs
  - Log files 
  - stdin (for piping)
- **Output**: SQLite database with normalized schema

### 2. Report Generator (`tools/reports/`)
- **Purpose**: Generate historical reports from the SQLite database
- **Report Types**: Cost analysis, User activity summaries
- **Export Formats**: CSV, PDF, JSON (Google Sheets integration stubbed)

### 3. Database Schema (`tools/logger/database.py`)
- **Sessions**: Session tracking with user and organization info
- **Metrics**: Time-series metrics data
- **Events**: Event logs with structured data
- **Costs**: Denormalized cost tracking for easy reporting
- **User Activity**: Denormalized user activity for analytics

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
make install-observability-tools

# Or manually:
pip install -r tools/requirements.txt
```

### 2. Start Background Logger

Choose one of the following based on your Claude Code setup:

#### Option A: Read from OpenTelemetry Collector Docker Logs (Recommended)
```bash
# Start the observability stack first
make up

# Start the background logger
make start-logger
```

#### Option B: Read from Log File
```bash
make start-logger-file LOG_FILE=/path/to/claude_code.log
```

#### Option C: Read from stdin (for piping)
```bash
# Pipe Claude Code output to the logger
claude --enable-logging 2>&1 | make start-logger-stdin
```

### 3. Generate Reports

```bash
# Generate weekly cost report
make generate-cost-report

# Generate weekly user activity report  
make generate-user-report

# Generate monthly reports (both cost and activity)
make generate-monthly-reports

# Generate custom period report
make generate-custom-report START_DATE=2024-01-01 END_DATE=2024-01-31 REPORT_TYPE=cost
```

### 4. Check Database Status

```bash
# Check if data is being collected
make check-db
```

## 📊 Metrics and Events Tracked

### Metrics
- `claude_code.session.count` - CLI sessions started
- `claude_code.lines_of_code.count` - Lines of code modified
- `claude_code.pull_request.count` - Pull requests created
- `claude_code.commit.count` - Git commits created
- `claude_code.cost.usage` - Cost of sessions by model
- `claude_code.token.usage` - Token usage (input/output/cache)
- `claude_code.code_edit_tool.decision` - Tool permission decisions

### Events
- `claude_code.user_prompt` - User prompt submissions
- `claude_code.tool_result` - Tool execution results and timings
- `claude_code.api_request` - API requests with duration and tokens
- `claude_code.api_error` - API errors with status codes
- `claude_code.tool_decision` - Tool permission decisions

## 🗄️ Database Schema

The SQLite database uses a normalized schema optimized for both real-time ingestion and reporting:

### Tables
- **sessions**: Session metadata and user information
- **metrics**: Time-series metrics with attributes
- **events**: Structured event logs
- **costs**: Denormalized cost data for easy reporting
- **user_activity**: Denormalized user activity for analytics

### Indexes
Optimized indexes on session_id, timestamp, and metric/event names for fast queries.

## 📈 Report Types

### Cost Reports
- **Total cost** breakdown by period
- **Model breakdown** - cost per Claude model
- **User breakdown** - cost per user  
- **Daily breakdown** - cost trends over time
- **Session summary** - session count and user metrics

### User Activity Reports
- **User statistics** - sessions, code changes, commits per user
- **Activity totals** - aggregate metrics across all users
- **Tool usage** - which Claude tools are used most
- **Productivity insights** - lines of code, PRs, commits

## 🔧 Advanced Usage

### Custom Report Generation

```bash
# Generate reports programmatically
cd tools/reports
python generate_reports.py \
  --report-type cost \
  --period custom \
  --start-date 2024-01-01 \
  --end-date 2024-03-31 \
  --format csv --format pdf --format json \
  --output-dir /path/to/reports
```

### Background Logger Options

```bash
cd tools/logger
python background_logger.py \
  --source /var/log/claude_code.log \
  --source-type file \
  --db-path /path/to/database.db \
  --log-level DEBUG
```

### Database Queries

Direct SQLite access for custom analysis:

```sql
-- Total cost by model last 30 days
SELECT model, SUM(cost_usd) as total_cost 
FROM costs 
WHERE timestamp > datetime('now', '-30 days')
GROUP BY model 
ORDER BY total_cost DESC;

-- Most active users
SELECT user_account_uuid, SUM(activity_count) as total_activity
FROM user_activity 
WHERE timestamp > datetime('now', '-7 days')
GROUP BY user_account_uuid 
ORDER BY total_activity DESC;

-- Daily session trends
SELECT DATE(timestamp) as date, COUNT(*) as sessions
FROM sessions 
WHERE start_time > datetime('now', '-30 days')
GROUP BY DATE(timestamp) 
ORDER BY date;
```

## 🔗 Integration with Existing Stack

This tooling complements the existing OpenTelemetry/Prometheus/Grafana stack:

- **Real-time monitoring**: Continue using Grafana dashboards for live metrics
- **Historical analysis**: Use these tools for detailed historical reports
- **Cost tracking**: Enhanced cost analysis not available in time-series DBs
- **User analytics**: DAU/WAU/MAU calculations and user behavior analysis

## 📝 Export Formats

### CSV Export
- Structured data with headers
- Raw data included for further analysis
- Compatible with Excel, Google Sheets, etc.

### PDF Export  
- Professional formatted reports
- Summary tables and charts
- Suitable for sharing with stakeholders

### JSON Export
- Machine-readable format
- Full data structure preserved
- API integration ready

### Google Sheets Integration (TODO)
Currently stubbed out. To implement:

1. Set up Google Sheets API credentials
2. Install additional dependencies: `pip install gspread google-auth`
3. Configure service account authentication
4. Implement worksheet creation and data insertion

## 🛠️ Configuration

### Environment Variables
- `CLAUDE_CODE_DB_PATH`: Path to SQLite database (default: `claude_code_observability.db`)
- `CLAUDE_CODE_LOG_LEVEL`: Logging level (default: `INFO`)
- `CLAUDE_CODE_REPORTS_DIR`: Default reports output directory (default: `reports/`)

### Claude Code Setup
Ensure Claude Code is configured with telemetry enabled:

```bash
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=otlp
export OTEL_LOGS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

## 🔍 Troubleshooting

### Common Issues

**Database not found**
```bash
# Check if logger is running and database exists
make check-db

# Start logger if not running
make start-logger
```

**No data being collected**
1. Verify Claude Code telemetry is enabled
2. Check OpenTelemetry collector is running: `docker ps`
3. Verify log parsing with debug mode: `--log-level DEBUG`

**PDF generation errors**
```bash
# Install reportlab if missing
pip install reportlab
```

**Permission errors**
```bash
# Ensure write permissions for database and reports directory
chmod 755 tools/
mkdir -p reports/
```

### Debugging

Enable debug logging to see parsed data:

```bash
cd tools/logger
python background_logger.py \
  --source otel-collector \
  --source-type docker \
  --log-level DEBUG
```

Check database contents:

```bash
sqlite3 claude_code_observability.db ".tables"
sqlite3 claude_code_observability.db "SELECT COUNT(*) FROM metrics;"
```

## 📋 Maintenance

### Database Cleanup
```bash
# Reset database (removes all data)
make clean-db

# Archive old data (manual SQL)
sqlite3 claude_code_observability.db "DELETE FROM metrics WHERE timestamp < datetime('now', '-90 days');"
```

### Log Rotation
For production deployments, consider setting up log rotation for the background logger process.

## 🤝 Contributing

When adding new metrics or events:

1. Update the parsing patterns in `background_logger.py`
2. Add database schema changes to `database.py`
3. Update report generation in `generate_reports.py`
4. Test with sample data
5. Update documentation

## 📚 References

- [Claude Code Observability Documentation](../../CLAUDE_OBSERVABILITY.md)
- [OpenTelemetry Specification](https://opentelemetry.io/docs/specs/)
- [SQLite Documentation](https://sqlite.org/docs.html)
- [ReportLab User Guide](https://www.reportlab.com/docs/reportlab-userguide.pdf)