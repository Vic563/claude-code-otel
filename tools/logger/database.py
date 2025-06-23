"""
SQLite database schema and operations for Claude Code observability metrics.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class ObservabilityDatabase:
    """Database handler for Claude Code observability data."""
    
    def __init__(self, db_path: str = "claude_code_observability.db"):
        self.db_path = Path(db_path)
        self.connection = None
        self.init_database()
    
    def connect(self):
        """Establish database connection."""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def init_database(self):
        """Initialize database schema."""
        with self.connect() as conn:
            # Sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    user_account_uuid TEXT,
                    organization_id TEXT,
                    app_version TEXT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    unit TEXT,
                    attributes TEXT, -- JSON blob for additional attributes
                    timestamp TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                )
            """)
            
            # Events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    event_name TEXT NOT NULL,
                    event_data TEXT, -- JSON blob for event attributes
                    timestamp TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                )
            """)
            
            # Cost tracking table (denormalized for easy reporting)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS costs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    model TEXT,
                    cost_usd REAL NOT NULL,
                    tokens_input INTEGER,
                    tokens_output INTEGER,
                    tokens_cache INTEGER,
                    timestamp TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                )
            """)
            
            # User activity table (denormalized for easy reporting)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_account_uuid TEXT,
                    activity_type TEXT NOT NULL, -- 'session', 'prompt', 'tool_usage', etc.
                    activity_count INTEGER DEFAULT 1,
                    lines_of_code_added INTEGER DEFAULT 0,
                    lines_of_code_removed INTEGER DEFAULT 0,
                    pull_requests INTEGER DEFAULT 0,
                    commits INTEGER DEFAULT 0,
                    timestamp TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                )
            """)
            
            # Create indexes for better query performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_session_id ON metrics (session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics (timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics (metric_name)")
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_session_id ON events (session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events (timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_name ON events (event_name)")
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_costs_session_id ON costs (session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_costs_timestamp ON costs (timestamp)")
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_activity_session_id ON user_activity (session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON user_activity (timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_activity_user ON user_activity (user_account_uuid)")
            
            conn.commit()
    
    def insert_session(self, session_id: str, user_account_uuid: Optional[str] = None,
                      organization_id: Optional[str] = None, app_version: Optional[str] = None,
                      start_time: Optional[datetime] = None):
        """Insert or update session information."""
        with self.connect() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO sessions 
                (session_id, user_account_uuid, organization_id, app_version, start_time)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, user_account_uuid, organization_id, app_version, start_time))
            conn.commit()
    
    def insert_metric(self, session_id: str, metric_name: str, metric_value: float,
                     unit: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None,
                     timestamp: Optional[datetime] = None):
        """Insert a metric record."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        attributes_json = json.dumps(attributes) if attributes else None
        
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO metrics 
                (session_id, metric_name, metric_value, unit, attributes, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, metric_name, metric_value, unit, attributes_json, timestamp))
            conn.commit()
    
    def insert_event(self, session_id: str, event_name: str, event_data: Optional[Dict[str, Any]] = None,
                    timestamp: Optional[datetime] = None):
        """Insert an event record."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        event_data_json = json.dumps(event_data) if event_data else None
        
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO events 
                (session_id, event_name, event_data, timestamp)
                VALUES (?, ?, ?, ?)
            """, (session_id, event_name, event_data_json, timestamp))
            conn.commit()
    
    def insert_cost(self, session_id: str, cost_usd: float, model: Optional[str] = None,
                   tokens_input: Optional[int] = None, tokens_output: Optional[int] = None,
                   tokens_cache: Optional[int] = None, timestamp: Optional[datetime] = None):
        """Insert a cost record."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO costs 
                (session_id, model, cost_usd, tokens_input, tokens_output, tokens_cache, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (session_id, model, cost_usd, tokens_input, tokens_output, tokens_cache, timestamp))
            conn.commit()
    
    def insert_user_activity(self, session_id: str, user_account_uuid: Optional[str],
                           activity_type: str, activity_count: int = 1,
                           lines_of_code_added: int = 0, lines_of_code_removed: int = 0,
                           pull_requests: int = 0, commits: int = 0,
                           timestamp: Optional[datetime] = None):
        """Insert user activity record."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO user_activity 
                (session_id, user_account_uuid, activity_type, activity_count,
                 lines_of_code_added, lines_of_code_removed, pull_requests, commits, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (session_id, user_account_uuid, activity_type, activity_count,
                  lines_of_code_added, lines_of_code_removed, pull_requests, commits, timestamp))
            conn.commit()
    
    def get_metrics_by_period(self, start_date: datetime, end_date: datetime,
                             metric_names: Optional[list] = None):
        """Get metrics for a specific time period."""
        with self.connect() as conn:
            query = """
                SELECT m.*, s.user_account_uuid, s.organization_id 
                FROM metrics m
                LEFT JOIN sessions s ON m.session_id = s.session_id
                WHERE m.timestamp BETWEEN ? AND ?
            """
            params = [start_date, end_date]
            
            if metric_names:
                placeholders = ','.join('?' * len(metric_names))
                query += f" AND m.metric_name IN ({placeholders})"
                params.extend(metric_names)
            
            query += " ORDER BY m.timestamp"
            
            return conn.execute(query, params).fetchall()
    
    def get_costs_by_period(self, start_date: datetime, end_date: datetime):
        """Get cost data for a specific time period."""
        with self.connect() as conn:
            return conn.execute("""
                SELECT c.*, s.user_account_uuid, s.organization_id 
                FROM costs c
                LEFT JOIN sessions s ON c.session_id = s.session_id
                WHERE c.timestamp BETWEEN ? AND ?
                ORDER BY c.timestamp
            """, (start_date, end_date)).fetchall()
    
    def get_user_activity_by_period(self, start_date: datetime, end_date: datetime):
        """Get user activity for a specific time period."""
        with self.connect() as conn:
            return conn.execute("""
                SELECT * FROM user_activity
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            """, (start_date, end_date)).fetchall()
    
    def get_session_summary(self, start_date: datetime, end_date: datetime):
        """Get session summary statistics."""
        with self.connect() as conn:
            return conn.execute("""
                SELECT 
                    COUNT(DISTINCT session_id) as total_sessions,
                    COUNT(DISTINCT user_account_uuid) as unique_users,
                    MIN(start_time) as earliest_session,
                    MAX(start_time) as latest_session
                FROM sessions
                WHERE start_time BETWEEN ? AND ?
            """, (start_date, end_date)).fetchone()