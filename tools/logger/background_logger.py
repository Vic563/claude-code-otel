"""
Background logger process for parsing Claude Code observability data.
Reads from OpenTelemetry collector logs or direct log files and stores in SQLite.
"""

import argparse
import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Generator, Union
import subprocess
import signal
import threading
from queue import Queue, Empty

# Auto-install missing dependencies
try:
    from auto_install import ensure_dependencies
    ensure_dependencies()
except ImportError:
    # auto_install not available, continue without it
    pass

from database import ObservabilityDatabase


class ObservabilityLogger:
    """Main logger class for processing Claude Code observability data."""
    
    def __init__(self, db_path: str = "claude_code_observability.db", 
                 log_level: str = "INFO"):
        self.db = ObservabilityDatabase(db_path)
        self.running = False
        self.log_queue = Queue()
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Metric parsing patterns
        self.metric_patterns = {
            'session_count': re.compile(r'claude_code\.session\.count.*?value:\s*(\d+\.?\d*)'),
            'lines_of_code': re.compile(r'claude_code\.lines_of_code\.count.*?value:\s*(\d+\.?\d*)'),
            'pull_request': re.compile(r'claude_code\.pull_request\.count.*?value:\s*(\d+\.?\d*)'),
            'commit': re.compile(r'claude_code\.commit\.count.*?value:\s*(\d+\.?\d*)'),
            'cost_usage': re.compile(r'claude_code\.cost\.usage.*?value:\s*(\d+\.?\d*)'),
            'token_usage': re.compile(r'claude_code\.token\.usage.*?value:\s*(\d+\.?\d*)'),
            'code_edit_tool': re.compile(r'claude_code\.code_edit_tool\.decision.*?value:\s*(\d+\.?\d*)')
        }
        
        # Event parsing patterns
        self.event_patterns = {
            'user_prompt': re.compile(r'claude_code\.user_prompt'),
            'tool_result': re.compile(r'claude_code\.tool_result'),
            'api_request': re.compile(r'claude_code\.api_request'),
            'api_error': re.compile(r'claude_code\.api_error'),
            'tool_decision': re.compile(r'claude_code\.tool_decision')
        }
        
        # Attribute extraction patterns
        self.attribute_patterns = {
            'session_id': re.compile(r'session\.id["\']:\s*["\']([^"\']+)["\']'),
            'user_account_uuid': re.compile(r'user\.account_uuid["\']:\s*["\']([^"\']+)["\']'),
            'organization_id': re.compile(r'organization\.id["\']:\s*["\']([^"\']+)["\']'),
            'app_version': re.compile(r'app\.version["\']:\s*["\']([^"\']+)["\']'),
            'model': re.compile(r'model["\']:\s*["\']([^"\']+)["\']'),
            'type': re.compile(r'type["\']:\s*["\']([^"\']+)["\']'),
        }
    
    def parse_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single log line for metrics and events."""
        try:
            # Try to parse as JSON first (structured logging)
            if line.strip().startswith('{'):
                return self._parse_json_log(line)
            else:
                return self._parse_text_log(line)
        except Exception as e:
            self.logger.debug(f"Failed to parse log line: {e}")
            return None
    
    def _parse_json_log(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse JSON structured log line."""
        try:
            data = json.loads(line.strip())
            
            # Extract timestamp
            timestamp = self._extract_timestamp(data)
            
            # Check if this is a metric or event
            if 'metric' in data or any(metric in line for metric in self.metric_patterns.keys()):
                return self._extract_metric_from_json(data, timestamp)
            elif 'event' in data or any(event in line for event in self.event_patterns.keys()):
                return self._extract_event_from_json(data, timestamp)
            
        except json.JSONDecodeError:
            pass
        
        return None
    
    def _parse_text_log(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse plain text log line."""
        # Extract timestamp from log line
        timestamp = self._extract_timestamp_from_text(line)
        
        # Check for metrics
        for metric_name, pattern in self.metric_patterns.items():
            match = pattern.search(line)
            if match:
                return self._extract_metric_from_text(line, metric_name, match, timestamp)
        
        # Check for events
        for event_name, pattern in self.event_patterns.items():
            if pattern.search(line):
                return self._extract_event_from_text(line, event_name, timestamp)
        
        return None
    
    def _extract_timestamp(self, data: Dict[str, Any]) -> datetime:
        """Extract timestamp from JSON data."""
        timestamp_fields = ['timestamp', 'time', '@timestamp', 'event.timestamp']
        
        for field in timestamp_fields:
            if field in data:
                return self._parse_timestamp(data[field])
        
        return datetime.utcnow()
    
    def _extract_timestamp_from_text(self, line: str) -> datetime:
        """Extract timestamp from text log line."""
        # Common timestamp patterns
        patterns = [
            re.compile(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[Z\d\.:+-]*)'),
            re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'),
            re.compile(r'(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})')
        ]
        
        for pattern in patterns:
            match = pattern.search(line)
            if match:
                return self._parse_timestamp(match.group(1))
        
        return datetime.utcnow()
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime object."""
        formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%m/%d/%Y %H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        return datetime.utcnow()
    
    def _extract_attributes(self, text: str) -> Dict[str, str]:
        """Extract common attributes from log text."""
        attributes = {}
        
        for attr_name, pattern in self.attribute_patterns.items():
            match = pattern.search(text)
            if match:
                attributes[attr_name] = match.group(1)
        
        return attributes
    
    def _extract_metric_from_json(self, data: Dict[str, Any], timestamp: datetime) -> Dict[str, Any]:
        """Extract metric information from JSON data."""
        metric_name = data.get('metric_name', 'unknown')
        metric_value = float(data.get('value', 0))
        unit = data.get('unit')
        
        # Extract attributes from the JSON data, including any session/user info
        attributes = data.get('attributes', {})
        for key, value in data.items():
            if key in ['session.id', 'user.account_uuid', 'organization.id', 'app.version', 'model', 'type']:
                attributes[key] = value
        
        return {
            'type': 'metric',
            'metric_name': metric_name,
            'metric_value': metric_value,
            'unit': unit,
            'attributes': attributes,
            'timestamp': timestamp
        }
    
    def _extract_metric_from_text(self, line: str, metric_name: str, match: re.Match, 
                                 timestamp: datetime) -> Dict[str, Any]:
        """Extract metric information from text log."""
        metric_value = float(match.group(1))
        attributes = self._extract_attributes(line)
        
        return {
            'type': 'metric',
            'metric_name': f'claude_code.{metric_name}',
            'metric_value': metric_value,
            'unit': self._get_metric_unit(metric_name),
            'attributes': attributes,
            'timestamp': timestamp
        }
    
    def _extract_event_from_json(self, data: Dict[str, Any], timestamp: datetime) -> Dict[str, Any]:
        """Extract event information from JSON data."""
        event_name = data.get('event_name', 'unknown')
        
        # Extract attributes, including any session/user info
        attributes = data.get('attributes', {})
        for key, value in data.items():
            if key not in ['event_name', 'timestamp'] and not key.startswith('_'):
                attributes[key] = value
        
        return {
            'type': 'event',
            'event_name': event_name,
            'event_data': attributes,
            'timestamp': timestamp
        }
    
    def _extract_event_from_text(self, line: str, event_name: str, timestamp: datetime) -> Dict[str, Any]:
        """Extract event information from text log."""
        attributes = self._extract_attributes(line)
        
        return {
            'type': 'event',
            'event_name': f'claude_code.{event_name}',
            'event_data': attributes,
            'timestamp': timestamp
        }
    
    def _get_metric_unit(self, metric_name: str) -> str:
        """Get the unit for a metric."""
        units = {
            'session_count': 'count',
            'lines_of_code': 'count',
            'pull_request': 'count',
            'commit': 'count',
            'cost_usage': 'USD',
            'token_usage': 'tokens',
            'code_edit_tool': 'count'
        }
        return units.get(metric_name, 'count')
    
    def process_parsed_data(self, data: Dict[str, Any]):
        """Process parsed data and store in database."""
        try:
            session_id = data['attributes'].get('session_id', 'unknown')
            
            # Ensure session exists
            self.db.insert_session(
                session_id=session_id,
                user_account_uuid=data['attributes'].get('user_account_uuid'),
                organization_id=data['attributes'].get('organization_id'),
                app_version=data['attributes'].get('app_version'),
                start_time=data['timestamp']
            )
            
            if data['type'] == 'metric':
                self._process_metric(data, session_id)
            elif data['type'] == 'event':
                self._process_event(data, session_id)
                
        except Exception as e:
            self.logger.error(f"Error processing data: {e}")
    
    def _process_metric(self, data: Dict[str, Any], session_id: str):
        """Process metric data."""
        # Store in metrics table
        self.db.insert_metric(
            session_id=session_id,
            metric_name=data['metric_name'],
            metric_value=data['metric_value'],
            unit=data['unit'],
            attributes=data['attributes'],
            timestamp=data['timestamp']
        )
        
        # Store specific metrics in denormalized tables for easier reporting
        metric_name = data['metric_name']
        metric_value = data['metric_value']
        attributes = data['attributes']
        
        if 'cost.usage' in metric_name:
            self.db.insert_cost(
                session_id=session_id,
                cost_usd=metric_value,
                model=attributes.get('model'),
                timestamp=data['timestamp']
            )
        
        elif any(x in metric_name for x in ['session.count', 'lines_of_code', 'pull_request', 'commit']):
            activity_type = metric_name.split('.')[-2]  # Extract activity type
            self.db.insert_user_activity(
                session_id=session_id,
                user_account_uuid=attributes.get('user_account_uuid'),
                activity_type=activity_type,
                activity_count=int(metric_value) if 'count' in metric_name else 0,
                lines_of_code_added=int(metric_value) if 'lines_of_code' in metric_name and attributes.get('type') == 'added' else 0,
                lines_of_code_removed=int(metric_value) if 'lines_of_code' in metric_name and attributes.get('type') == 'removed' else 0,
                pull_requests=int(metric_value) if 'pull_request' in metric_name else 0,
                commits=int(metric_value) if 'commit' in metric_name else 0,
                timestamp=data['timestamp']
            )
    
    def _process_event(self, data: Dict[str, Any], session_id: str):
        """Process event data."""
        self.db.insert_event(
            session_id=session_id,
            event_name=data['event_name'],
            event_data=data['event_data'],
            timestamp=data['timestamp']
        )
    
    def read_from_file(self, file_path: str) -> Generator[str, None, None]:
        """Read log lines from a file."""
        try:
            with open(file_path, 'r') as f:
                # Start from end of file for live tailing
                f.seek(0, 2)
                while self.running:
                    line = f.readline()
                    if line:
                        yield line.strip()
                    else:
                        time.sleep(0.1)  # Short sleep to avoid busy waiting
        except FileNotFoundError:
            self.logger.error(f"Log file not found: {file_path}")
        except Exception as e:
            self.logger.error(f"Error reading from file {file_path}: {e}")
    
    def read_from_stdin(self) -> Generator[str, None, None]:
        """Read log lines from stdin."""
        try:
            while self.running:
                line = sys.stdin.readline()
                if line:
                    yield line.strip()
                else:
                    time.sleep(0.1)
        except Exception as e:
            self.logger.error(f"Error reading from stdin: {e}")
    
    def read_from_docker_logs(self, container_name: str) -> Generator[str, None, None]:
        """Read log lines from Docker container logs."""
        try:
            cmd = ['docker', 'logs', '-f', container_name]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                     universal_newlines=True, bufsize=1)
            
            while self.running and process.poll() is None:
                line = process.stdout.readline()
                if line:
                    yield line.strip()
                else:
                    time.sleep(0.1)
                    
        except Exception as e:
            self.logger.error(f"Error reading from Docker container {container_name}: {e}")
    
    def start_logging(self, source: str, source_type: str = "file"):
        """Start the logging process."""
        self.running = True
        self.logger.info(f"Starting observability logger from {source_type}: {source}")
        
        # Choose the appropriate reader
        if source_type == "file":
            log_reader = self.read_from_file(source)
        elif source_type == "stdin":
            log_reader = self.read_from_stdin()
        elif source_type == "docker":
            log_reader = self.read_from_docker_logs(source)
        else:
            raise ValueError(f"Unknown source type: {source_type}")
        
        # Process log lines
        for line in log_reader:
            if not self.running:
                break
                
            parsed_data = self.parse_log_line(line)
            if parsed_data:
                self.process_parsed_data(parsed_data)
                self.logger.debug(f"Processed: {parsed_data['type']} - {parsed_data.get('metric_name', parsed_data.get('event_name'))}")
    
    def stop_logging(self):
        """Stop the logging process."""
        self.logger.info("Stopping observability logger")
        self.running = False
        self.db.close()


def signal_handler(signum, frame, logger: ObservabilityLogger):
    """Handle shutdown signals."""
    logger.stop_logging()
    sys.exit(0)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Claude Code Observability Background Logger")
    parser.add_argument("--source", required=True, help="Log source (file path, container name, or 'stdin')")
    parser.add_argument("--source-type", choices=["file", "stdin", "docker"], default="file",
                       help="Type of log source")
    parser.add_argument("--db-path", default="claude_code_observability.db",
                       help="Path to SQLite database file")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO",
                       help="Logging level")
    
    args = parser.parse_args()
    
    # Create logger instance
    logger = ObservabilityLogger(db_path=args.db_path, log_level=args.log_level)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, logger))
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, logger))
    
    try:
        logger.start_logging(args.source, args.source_type)
    except KeyboardInterrupt:
        logger.stop_logging()
    except Exception as e:
        logger.logger.error(f"Fatal error: {e}")
        logger.stop_logging()
        sys.exit(1)


if __name__ == "__main__":
    main()