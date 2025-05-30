import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

class DataLogger:
    def __init__(self, log_file: str = 'rover_log.json', max_entries: int = 500):
        """
        Initialize data logger
        
        Args:
            log_file: Path to the log file
            max_entries: Maximum number of entries to keep in log
        """
        self.log_file = log_file
        self.max_entries = max_entries
        self.logs = []
        
        self._load_existing_logs()
    
    def _load_existing_logs(self):
        """Load existing logs from file"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    self.logs = json.load(f)
                print(f"Loaded {len(self.logs)} existing log entries")
            else:
                self.logs = []
                print("Starting with empty log file")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading logs, starting fresh: {e}")
            self.logs = []
    
    def _save_logs(self):
        """Save logs to file"""
        try:
            # Keep only the most recent entries
            if len(self.logs) > self.max_entries:
                self.logs = self.logs[-self.max_entries:]
            
            with open(self.log_file, 'w') as f:
                json.dump(self.logs, f, indent=2)
        except Exception as e:
            print(f"Error saving logs: {e}")
    
    def log_sensor_data(self, distance: Optional[int], object_detected: bool):
        """
        Log ultrasonic sensor data
        
        Args:
            distance: Distance measurement in cm
            object_detected: Whether an object was detected
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "sensor",
            "distance_cm": distance,
            "object_detected": object_detected,
            "status": "object_detected" if object_detected else "clear_path"
        }
        
        self._add_log_entry(log_entry)
    
    def log_color_detection(self, color: Optional[str], material: Optional[str], 
                          confidence: float, detected: bool):
        """
        Log color detection data
        
        Args:
            color: Detected color name
            material: Associated material type
            confidence: Detection confidence percentage
            detected: Whether color was detected
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "color_detection",
            "color_detected": color,
            "material_type": material,
            "confidence": confidence,
            "detected": detected,
            "status": f"{color}_detected" if detected else "no_target"
        }
        
        self._add_log_entry(log_entry)
    
    def log_mining_action(self, distance: Optional[int], color: Optional[str], 
                         material: Optional[str], confidence: float, 
                         action_successful: bool):
        """
        Log mining action
        
        Args:
            distance: Distance to target
            color: Target color
            material: Target material
            confidence: Detection confidence
            action_successful: Whether mining action was successful
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "mining",
            "distance_cm": distance,
            "target_color": color,
            "target_material": material,
            "confidence": confidence,
            "action_successful": action_successful,
            "status": "mining_success" if action_successful else "mining_failed"
        }
        
        self._add_log_entry(log_entry)
    
    def log_system_event(self, event_type: str, message: str, 
                        additional_data: Optional[Dict] = None):
        """
        Log system events
        
        Args:
            event_type: Type of event ('startup', 'shutdown', 'error', 'info')
            message: Event message
            additional_data: Additional event data
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "system",
            "event_type": event_type,
            "message": message,
            "status": event_type
        }
        
        if additional_data:
            log_entry.update(additional_data)
        
        self._add_log_entry(log_entry)
    
    def log_led_event(self, led_name: str, action: str, duration: Optional[float] = None):
        """
        Log LED events
        
        Args:
            led_name: Name of the LED
            action: Action performed ('on', 'off', 'blink', 'toggle')
            duration: Duration for timed actions
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "led",
            "led_name": led_name,
            "action": action,
            "duration": duration,
            "status": f"led_{action}"
        }
        
        self._add_log_entry(log_entry)
    
    def _add_log_entry(self, log_entry: Dict):
        """
        Add log entry and save to file
        
        Args:
            log_entry: Log entry dictionary
        """
        self.logs.append(log_entry)
        self._save_logs()
    
    def get_logs(self, log_type: Optional[str] = None, 
                limit: Optional[int] = None) -> List[Dict]:
        """
        Get logs with optional filtering
        
        Args:
            log_type: Filter by log type
            limit: Limit number of returned entries
            
        Returns:
            List of log entries
        """
        filtered_logs = self.logs
        
        if log_type:
            filtered_logs = [log for log in filtered_logs if log.get('type') == log_type]
        
        if limit:
            filtered_logs = filtered_logs[-limit:]
        
        return filtered_logs
    
    def get_recent_logs(self, minutes: int = 60) -> List[Dict]:
        """
        Get logs from the last N minutes
        
        Args:
            minutes: Number of minutes to look back
            
        Returns:
            List of recent log entries
        """
        from datetime import datetime, timedelta
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_logs = []
        
        for log in self.logs:
            try:
                log_time = datetime.fromisoformat(log['timestamp'])
                if log_time >= cutoff_time:
                    recent_logs.append(log)
            except (KeyError, ValueError):
                continue
        
        return recent_logs
    
    def get_statistics(self) -> Dict:
        """
        Get logging statistics
        
        Returns:
            Dictionary with various statistics
        """
        total_logs = len(self.logs)
        
        # Count by type
        type_counts = {}
        status_counts = {}
        
        for log in self.logs:
            log_type = log.get('type', 'unknown')
            status = log.get('status', 'unknown')
            
            type_counts[log_type] = type_counts.get(log_type, 0) + 1
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Recent activity (last hour)
        recent_logs = self.get_recent_logs(60)
        
        return {
            "total_entries": total_logs,
            "entries_by_type": type_counts,
            "entries_by_status": status_counts,
            "recent_activity_count": len(recent_logs),
            "log_file": self.log_file,
            "max_entries": self.max_entries
        }
    
    def clear_logs(self):
        """Clear all logs"""
        self.logs = []
        self._save_logs()
        print("All logs cleared")
    
    def export_logs(self, export_file: str) -> bool:
        """
        Export logs to a different file
        
        Args:
            export_file: Path to export file
            
        Returns:
            Success status
        """
        try:
            with open(export_file, 'w') as f:
                json.dump(self.logs, f, indent=2)
            print(f"Logs exported to {export_file}")
            return True
        except Exception as e:
            print(f"Error exporting logs: {e}")
            return False
            