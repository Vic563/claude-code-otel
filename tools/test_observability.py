#!/usr/bin/env python3
"""
Test script for Claude Code observability tools.
Creates sample data and generates test reports.
"""

import json
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add tools to path
sys.path.append(str(Path(__file__).parent / "logger"))
sys.path.append(str(Path(__file__).parent / "reports"))

from database import ObservabilityDatabase
from generate_reports import ReportGenerator


def create_sample_data(db: ObservabilityDatabase):
    """Create sample data for testing."""
    print("Creating sample data...")
    
    # Create sample sessions
    session_ids = [
        "session_001_user_alice",
        "session_002_user_bob", 
        "session_003_user_alice",
        "session_004_user_charlie"
    ]
    
    users = {
        "session_001_user_alice": "alice@company.com",
        "session_002_user_bob": "bob@company.com",
        "session_003_user_alice": "alice@company.com",
        "session_004_user_charlie": "charlie@company.com"
    }
    
    base_time = datetime.utcnow() - timedelta(days=7)
    
    for i, session_id in enumerate(session_ids):
        # Create session
        session_time = base_time + timedelta(hours=i*6)
        db.insert_session(
            session_id=session_id,
            user_account_uuid=users[session_id],
            organization_id="org_123",
            app_version="1.0.0",
            start_time=session_time
        )
        
        # Add metrics
        for j in range(5):  # 5 metrics per session
            metric_time = session_time + timedelta(minutes=j*10)
            
            # Session count
            db.insert_metric(
                session_id=session_id,
                metric_name="claude_code.session.count",
                metric_value=1,
                unit="count",
                timestamp=metric_time
            )
            
            # Lines of code
            db.insert_metric(
                session_id=session_id,
                metric_name="claude_code.lines_of_code.count",
                metric_value=25 + j*5,
                unit="count",
                attributes={"type": "added"},
                timestamp=metric_time
            )
            
            # Cost
            cost_value = 0.05 + (j * 0.02)
            db.insert_metric(
                session_id=session_id,
                metric_name="claude_code.cost.usage",
                metric_value=cost_value,
                unit="USD",
                attributes={"model": "claude-3-sonnet"},
                timestamp=metric_time
            )
            
            # Token usage
            db.insert_metric(
                session_id=session_id,
                metric_name="claude_code.token.usage",
                metric_value=150 + j*20,
                unit="tokens",
                attributes={"type": "input"},
                timestamp=metric_time
            )
        
        # Add cost records
        for j in range(3):
            cost_time = session_time + timedelta(minutes=j*15)
            db.insert_cost(
                session_id=session_id,
                cost_usd=0.08 + j*0.03,
                model="claude-3-sonnet",
                tokens_input=120 + j*30,
                tokens_output=80 + j*20,
                timestamp=cost_time
            )
        
        # Add user activity
        db.insert_user_activity(
            session_id=session_id,
            user_account_uuid=users[session_id],
            activity_type="session",
            activity_count=1,
            lines_of_code_added=75 + i*25,
            lines_of_code_removed=10 + i*5,
            pull_requests=1 if i % 2 == 0 else 0,
            commits=2 + i,
            timestamp=session_time
        )
        
        # Add events
        for j in range(3):
            event_time = session_time + timedelta(minutes=j*20)
            
            # User prompt event
            db.insert_event(
                session_id=session_id,
                event_name="claude_code.user_prompt",
                event_data={
                    "prompt_length": 150 + j*50,
                    "prompt": "[REDACTED]"
                },
                timestamp=event_time
            )
            
            # Tool result event
            db.insert_event(
                session_id=session_id,
                event_name="claude_code.tool_result",
                event_data={
                    "name": "str_replace_editor",
                    "success": "true",
                    "duration_ms": 250 + j*100
                },
                timestamp=event_time
            )
    
    print(f"✅ Created sample data for {len(session_ids)} sessions")


def test_database_operations(db: ObservabilityDatabase):
    """Test basic database operations."""
    print("\nTesting database operations...")
    
    # Test queries
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    # Test metrics query
    metrics = db.get_metrics_by_period(start_date, end_date)
    print(f"  📊 Found {len(metrics)} metrics")
    
    # Test costs query
    costs = db.get_costs_by_period(start_date, end_date)
    print(f"  💰 Found {len(costs)} cost records")
    
    # Test user activity query
    activities = db.get_user_activity_by_period(start_date, end_date)
    print(f"  👥 Found {len(activities)} activity records")
    
    # Test session summary
    summary = db.get_session_summary(start_date, end_date)
    if summary:
        print(f"  📈 Session summary: {summary['total_sessions']} sessions, {summary['unique_users']} users")
    
    print("✅ Database operations test completed")


def test_report_generation():
    """Test report generation."""
    print("\nTesting report generation...")
    
    generator = ReportGenerator(db_path="test_observability.db")
    
    # Test cost report
    print("  Generating cost report...")
    cost_report = generator.generate_cost_report("week")
    print(f"    Total cost: ${cost_report['total_cost']}")
    print(f"    Models: {list(cost_report['model_breakdown'].keys())}")
    print(f"    Users: {len(cost_report['user_breakdown'])} users")
    
    # Test user activity report  
    print("  Generating user activity report...")
    activity_report = generator.generate_user_activity_report("week")
    print(f"    Unique users: {activity_report['unique_users']}")
    print(f"    Total sessions: {activity_report['activity_totals']['total_sessions']}")
    print(f"    Total commits: {activity_report['activity_totals']['total_commits']}")
    
    # Test CSV export
    print("  Testing CSV export...")
    output_dir = Path("test_reports")
    output_dir.mkdir(exist_ok=True)
    
    csv_file = output_dir / "test_cost_report.csv"
    generator.export_to_csv(cost_report, str(csv_file), "cost")
    print(f"    Created: {csv_file}")
    
    csv_file = output_dir / "test_activity_report.csv"
    generator.export_to_csv(activity_report, str(csv_file), "user_activity")
    print(f"    Created: {csv_file}")
    
    # Test JSON export
    json_file = output_dir / "test_cost_report.json"
    with open(json_file, 'w') as f:
        json.dump(cost_report, f, indent=2, default=str)
    print(f"    Created: {json_file}")
    
    print("✅ Report generation test completed")


def test_log_parsing():
    """Test log parsing functionality."""
    print("\nTesting log parsing...")
    
    # Import background logger
    from background_logger import ObservabilityLogger
    
    logger = ObservabilityLogger(db_path="test_observability.db")
    
    # Test sample log lines
    test_logs = [
        '{"timestamp": "2024-01-15T10:30:00Z", "metric_name": "claude_code.session.count", "value": 1, "attributes": {"session.id": "test_session_123", "user.account_uuid": "test_user@example.com"}}',
        'INFO 2024-01-15T10:31:00Z claude_code.cost.usage value: 0.12 session.id: "test_session_123" model: "claude-3-sonnet"',
        '{"event_name": "claude_code.user_prompt", "timestamp": "2024-01-15T10:32:00Z", "attributes": {"session.id": "test_session_123", "prompt_length": 200}}',
    ]
    
    parsed_count = 0
    for log_line in test_logs:
        parsed = logger.parse_log_line(log_line)
        if parsed:
            parsed_count += 1
            print(f"    ✅ Parsed: {parsed['type']} - {parsed.get('metric_name', parsed.get('event_name'))}")
        else:
            print(f"    ❌ Failed to parse: {log_line[:50]}...")
    
    print(f"✅ Log parsing test completed: {parsed_count}/{len(test_logs)} lines parsed")


def main():
    """Run all tests."""
    print("🧪 Claude Code Observability Tools Test Suite")
    print("=" * 50)
    
    # Clean up any existing test database
    test_db_path = Path("test_observability.db")
    if test_db_path.exists():
        test_db_path.unlink()
    
    try:
        # Initialize database
        db = ObservabilityDatabase(db_path="test_observability.db")
        print("✅ Database initialized")
        
        # Run tests
        create_sample_data(db)
        test_database_operations(db)
        test_log_parsing()
        test_report_generation()
        
        print("\n" + "=" * 50)
        print("🎉 All tests completed successfully!")
        print("\nGenerated files:")
        print("  - test_observability.db (SQLite database)")
        print("  - test_reports/ (CSV and JSON reports)")
        print("\nTo clean up test files:")
        print("  rm -rf test_observability.db test_reports/")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        # Close database connection
        if 'db' in locals():
            db.close()
    
    return 0


if __name__ == "__main__":
    exit(main())