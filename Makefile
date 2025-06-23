# Claude Code Observability Stack
.PHONY: help up down logs restart clean validate-config

help: ## Show this help message
	@echo "Claude Code Observability Stack"
	@echo "================================"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Start the observability stack
	@echo "🚀 Starting Claude Code observability stack..."
	docker compose up -d
	@echo "✅ Stack started!"
	@echo "📊 Grafana: http://localhost:3000 (admin/admin)"
	@echo "🔍 Prometheus: http://localhost:9090"
	@echo "📄 Loki: http://localhost:3100"


down: ## Stop the observability stack
	@echo "🛑 Stopping Claude Code observability stack..."
	docker compose down
	@echo "✅ Stack stopped!"

restart: ## Restart the observability stack
	@echo "🔄 Restarting Claude Code observability stack..."
	docker compose restart
	@echo "✅ Stack restarted!"

logs: ## Show logs from all services
	docker compose logs -f

logs-collector: ## Show OpenTelemetry collector logs
	docker compose logs -f otel-collector

logs-prometheus: ## Show Prometheus logs
	docker compose logs -f prometheus

logs-grafana: ## Show Grafana logs
	docker compose logs -f grafana

clean: ## Clean up containers and volumes
	@echo "🧹 Cleaning up..."
	docker compose down -v
	docker system prune -f
	@echo "✅ Cleanup complete!"





validate-config: ## Validate all configuration files
	@echo "✅ Validating configurations..."
	@echo "📋 Checking docker compose.yml..."
	docker compose config > /dev/null && echo "✅ docker compose.yml is valid"
	@echo "📋 Checking collector-config.yaml..."
	@if command -v otelcol-contrib >/dev/null 2>&1; then \
		otelcol-contrib --config-validate --config=collector-config.yaml; \
	else \
		echo "ℹ️  Install otelcol-contrib to validate collector config"; \
	fi


status: ## Show stack status
	@echo "📊 Claude Code Observability Stack Status"
	@echo "==========================================="
	@docker compose ps
	@echo ""
	@echo "🌐 Service URLs:"
	@echo "  Grafana:      http://localhost:3000"
	@echo "  Prometheus:   http://localhost:9090"
	@echo "  Loki:         http://localhost:3100"

	@echo "  Collector:    http://localhost:4317 (gRPC), http://localhost:4318 (HTTP)"

setup-claude: ## Display Claude Code telemetry setup instructions
	@echo "🤖 Claude Code Telemetry Setup"
	@echo "==============================="
	@echo ""
	@echo "To enable telemetry in Claude Code, set these environment variables:"
	@echo ""
	@echo "export CLAUDE_CODE_ENABLE_TELEMETRY=1"
	@echo "export OTEL_METRICS_EXPORTER=otlp"
	@echo "export OTEL_LOGS_EXPORTER=otlp"
	@echo "export OTEL_EXPORTER_OTLP_PROTOCOL=grpc"
	@echo "export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317"
	@echo ""
	@echo "For debugging (faster export intervals):"
	@echo "export OTEL_METRIC_EXPORT_INTERVAL=10000"
	@echo "export OTEL_LOGS_EXPORT_INTERVAL=5000"
	@echo ""
	@echo "Then run: claude"

demo-metrics: ## Generate demo metrics for testing
	@echo "🎯 This would generate demo metrics if Claude Code was running"
	@echo "💡 To see real metrics, ensure Claude Code is configured with telemetry enabled"
	@echo "📖 Run 'make setup-claude' for setup instructions"

# Observability setup and management targets
setup-observability: ## Complete setup of observability tools (plug-and-play)
	@echo "🚀 Setting up Claude Code observability tools..."
	python setup_observability.py
	@echo "✅ Setup complete! Ready to use."

install-observability-tools: ## Install Python dependencies for observability tools (legacy)
	@echo "📦 Installing observability tools dependencies..."
	@echo "💡 Consider using 'make setup-observability' for a better experience"
	pip install -r tools/requirements.txt
	@echo "✅ Dependencies installed!"

check-observability-setup: ## Check if observability tools are properly set up
	@echo "🔍 Checking observability tools setup..."
	@if [ -d "venv_observability" ]; then \
		echo "✅ Virtual environment exists"; \
		./venv_observability/bin/python -c "import sqlite3; import csv; print('✅ Core dependencies available')" 2>/dev/null || echo "❌ Core dependencies missing"; \
		if [ -f "tools/reports/generate_reports.py" ]; then \
			echo "✅ Report generator available"; \
		else \
			echo "❌ Report generator missing"; \
		fi; \
		if [ -f "tools/logger/background_logger.py" ]; then \
			echo "✅ Background logger available"; \
		else \
			echo "❌ Background logger missing"; \
		fi; \
	else \
		echo "❌ Virtual environment not found"; \
		echo "💡 Run 'make setup-observability' to set up"; \
	fi

start-logger: check-observability-setup ## Start the background observability logger
	@echo "🚀 Starting Claude Code observability background logger..."
	@echo "📊 Reading from OpenTelemetry collector logs..."
	@if [ -d "venv_observability" ]; then \
		./venv_observability/bin/python tools/logger/background_logger.py \
			--source otel-collector \
			--source-type docker \
			--db-path claude_code_observability.db \
			--log-level INFO; \
	else \
		echo "❌ Virtual environment not found. Run 'make setup-observability' first"; \
		exit 1; \
	fi

start-logger-file: check-observability-setup ## Start logger reading from a log file
	@echo "🚀 Starting Claude Code observability logger (file mode)..."
	@echo "📝 Usage: make start-logger-file LOG_FILE=/path/to/logfile"
	@if [ -z "$(LOG_FILE)" ]; then \
		echo "❌ Error: LOG_FILE parameter required"; \
		echo "   Example: make start-logger-file LOG_FILE=/tmp/claude_code.log"; \
		exit 1; \
	fi
	@if [ -d "venv_observability" ]; then \
		./venv_observability/bin/python tools/logger/background_logger.py \
			--source $(LOG_FILE) \
			--source-type file \
			--db-path claude_code_observability.db \
			--log-level INFO; \
	else \
		echo "❌ Virtual environment not found. Run 'make setup-observability' first"; \
		exit 1; \
	fi

start-logger-stdin: check-observability-setup ## Start logger reading from stdin
	@echo "🚀 Starting Claude Code observability logger (stdin mode)..."
	@echo "📥 Pipe your logs to this command"
	@if [ -d "venv_observability" ]; then \
		./venv_observability/bin/python tools/logger/background_logger.py \
			--source stdin \
			--source-type stdin \
			--db-path claude_code_observability.db \
			--log-level INFO; \
	else \
		echo "❌ Virtual environment not found. Run 'make setup-observability' first"; \
		exit 1; \
	fi

generate-cost-report: check-observability-setup ## Generate weekly cost report (CSV + PDF)
	@echo "💰 Generating weekly cost report..."
	@mkdir -p reports
	@if [ -d "venv_observability" ]; then \
		./venv_observability/bin/python tools/reports/generate_reports.py \
			--report-type cost \
			--period week \
			--format csv --format pdf \
			--db-path claude_code_observability.db \
			--output-dir reports; \
	else \
		echo "❌ Virtual environment not found. Run 'make setup-observability' first"; \
		exit 1; \
	fi
	@echo "✅ Cost report generated in reports/ directory"

generate-user-report: check-observability-setup ## Generate weekly user activity report (CSV + PDF)
	@echo "👥 Generating weekly user activity report..."
	@mkdir -p reports
	@if [ -d "venv_observability" ]; then \
		./venv_observability/bin/python tools/reports/generate_reports.py \
			--report-type user_activity \
			--period week \
			--format csv --format pdf \
			--db-path claude_code_observability.db \
			--output-dir reports; \
	else \
		echo "❌ Virtual environment not found. Run 'make setup-observability' first"; \
		exit 1; \
	fi
	@echo "✅ User activity report generated in reports/ directory"

generate-monthly-reports: check-observability-setup ## Generate monthly cost and user activity reports
	@echo "📊 Generating monthly reports..."
	@mkdir -p reports
	@if [ -d "venv_observability" ]; then \
		./venv_observability/bin/python tools/reports/generate_reports.py \
			--report-type cost \
			--period month \
			--format csv --format pdf --format json \
			--db-path claude_code_observability.db \
			--output-dir reports; \
		./venv_observability/bin/python tools/reports/generate_reports.py \
			--report-type user_activity \
			--period month \
			--format csv --format pdf --format json \
			--db-path claude_code_observability.db \
			--output-dir reports; \
	else \
		echo "❌ Virtual environment not found. Run 'make setup-observability' first"; \
		exit 1; \
	fi
	@echo "✅ Monthly reports generated in reports/ directory"

generate-custom-report: check-observability-setup ## Generate custom period report (requires START_DATE and END_DATE)
	@echo "📅 Generating custom period report..."
	@if [ -z "$(START_DATE)" ] || [ -z "$(END_DATE)" ] || [ -z "$(REPORT_TYPE)" ]; then \
		echo "❌ Error: START_DATE, END_DATE, and REPORT_TYPE parameters required"; \
		echo "   Example: make generate-custom-report START_DATE=2024-01-01 END_DATE=2024-01-31 REPORT_TYPE=cost"; \
		exit 1; \
	fi
	@mkdir -p reports
	@if [ -d "venv_observability" ]; then \
		./venv_observability/bin/python tools/reports/generate_reports.py \
			--report-type $(REPORT_TYPE) \
			--period custom \
			--start-date $(START_DATE) \
			--end-date $(END_DATE) \
			--format csv --format pdf \
			--db-path claude_code_observability.db \
			--output-dir reports; \
	else \
		echo "❌ Virtual environment not found. Run 'make setup-observability' first"; \
		exit 1; \
	fi
	@echo "✅ Custom report generated in reports/ directory"

check-db: ## Check database status and show recent entries
	@echo "🗄️  Checking observability database status..."
	@if [ -f claude_code_observability.db ]; then \
		echo "✅ Database exists"; \
		sqlite3 claude_code_observability.db "SELECT 'Sessions: ' || COUNT(*) FROM sessions UNION ALL SELECT 'Metrics: ' || COUNT(*) FROM metrics UNION ALL SELECT 'Events: ' || COUNT(*) FROM events UNION ALL SELECT 'Costs: ' || COUNT(*) FROM costs;"; \
		echo "📊 Recent entries:"; \
		sqlite3 claude_code_observability.db "SELECT 'Latest metric: ' || metric_name || ' = ' || metric_value || ' (' || datetime(timestamp) || ')' FROM metrics ORDER BY timestamp DESC LIMIT 1;"; \
		sqlite3 claude_code_observability.db "SELECT 'Latest event: ' || event_name || ' (' || datetime(timestamp) || ')' FROM events ORDER BY timestamp DESC LIMIT 1;"; \
	else \
		echo "❌ Database not found. Start the logger first with 'make start-logger'"; \
	fi

clean-db: ## Clean/reset the observability database
	@echo "🧹 Cleaning observability database..."
	@if [ -f claude_code_observability.db ]; then \
		rm claude_code_observability.db; \
		echo "✅ Database cleaned"; \
	else \
		echo "ℹ️  No database to clean"; \
	fi

test-observability: check-observability-setup ## Test the observability tools with sample data
	@echo "🧪 Testing observability tools..."
	@if [ -d "venv_observability" ]; then \
		./venv_observability/bin/python tools/test_observability.py; \
	else \
		echo "❌ Virtual environment not found. Run 'make setup-observability' first"; \
		exit 1; \
	fi
	@echo "✅ Test completed - check test_reports/ for generated files" 