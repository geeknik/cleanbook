"""
Scheduler Module - Temporal Orchestration for Automated Purification
Manages scheduled cleanup operations with system integration
"""

import os
import sys
import time
import datetime
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
import logging
from enum import Enum, auto


class ScheduleFrequency(Enum):
    """Temporal frequencies for scheduled operations"""
    DAILY = auto()
    WEEKLY = auto()
    MONTHLY = auto()


class Scheduler:
    """
    Temporal orchestrator for automated cleanup operations.
    Manages scheduled execution with system integration capabilities.
    """
    
    def __init__(self, config_path: Path, logger):
        """
        Initialize the temporal orchestrator.
        
        Args:
            config_path: Path to configuration file
            logger: Logging consciousness for operation tracking
        """
        self.config_path = config_path
        self.logger = logger
        self.config = self._load_config()
        self.schedule_enabled = self.config.get('scheduling', {}).get('enabled', False)
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from the sacred text"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.log_error(e, "config_loading")
            return {}
    
    def is_scheduled_time(self) -> bool:
        """
        Determine if current time matches scheduled execution window.
        
        Returns:
            True if it's time for scheduled cleanup
        """
        if not self.schedule_enabled:
            return False
            
        schedule_config = self.config.get('scheduling', {})
        frequency = schedule_config.get('frequency', 'weekly')
        hour = schedule_config.get('hour', 3)
        minute = schedule_config.get('minute', 30)
        
        now = datetime.datetime.now()
        
        if frequency == 'daily':
            return now.hour == hour and now.minute == minute
        elif frequency == 'weekly':
            day_of_week = schedule_config.get('day_of_week', 1)  # Monday = 1
            return (now.weekday() == (day_of_week - 1) and 
                   now.hour == hour and now.minute == minute)
        elif frequency == 'monthly':
            # First day of month at specified time
            return (now.day == 1 and now.hour == hour and now.minute == minute)
            
        return False
    
    def setup_system_schedule(self) -> bool:
        """
        Configure system-level scheduling (launchd on macOS).
        
        Returns:
            True if scheduling was successfully configured
        """
        try:
            schedule_config = self.config.get('scheduling', {})
            frequency = schedule_config.get('frequency', 'weekly')
            hour = schedule_config.get('hour', 3)
            minute = schedule_config.get('minute', 30)
            
            # Create launchd plist content
            plist_content = self._generate_launchd_plist(frequency, hour, minute)
            
            # Write plist to user's LaunchAgents directory
            launch_agents_dir = Path.home() / "Library/LaunchAgents"
            launch_agents_dir.mkdir(exist_ok=True)
            
            plist_path = launch_agents_dir / "com.cleanbook.scheduler.plist"
            with open(plist_path, 'w') as f:
                f.write(plist_content)
            
            # Load the launchd job
            subprocess.run(['launchctl', 'load', str(plist_path)], check=True)
            
            self.logger.logger.info(f"✅ System schedule configured: {plist_path}")
            return True
            
        except Exception as e:
            self.logger.log_error(e, "system_schedule_setup")
            return False
    
    def _generate_launchd_plist(self, frequency: str, hour: int, minute: int) -> str:
        """Generate launchd plist content for system scheduling"""
        script_path = Path(__file__).parent.parent / "cleanbook.py"
        
        # Ensure secure log directory exists
        log_dir = Path.home() / "Library/Logs"
        log_dir.mkdir(mode=0o750, exist_ok=True)
        
        # Create secure log paths
        stdout_log = log_dir / "cleanbook.log"
        stderr_log = log_dir / "cleanbook.error.log"
        
        if frequency == 'daily':
            interval = 86400  # 24 hours in seconds
        elif frequency == 'weekly':
            interval = 604800  # 7 days in seconds
        elif frequency == 'monthly':
            interval = 2592000  # 30 days in seconds
        else:
            interval = 604800  # Default to weekly
        
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cleanbook.scheduler</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{script_path}</string>
        <string>--clean</string>
        <string>--force</string>
    </array>
    <key>StartInterval</key>
    <integer>{interval}</integer>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>{hour}</integer>
        <key>Minute</key>
        <integer>{minute}</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{stdout_log}</string>
    <key>StandardErrorPath</key>
    <string>{stderr_log}</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>"""
    
    def remove_system_schedule(self) -> bool:
        """
        Remove system-level scheduling configuration.
        
        Returns:
            True if scheduling was successfully removed
        """
        try:
            plist_path = Path.home() / "Library/LaunchAgents/com.cleanbook.scheduler.plist"
            
            if plist_path.exists():
                # Unload the launchd job
                subprocess.run(['launchctl', 'unload', str(plist_path)], check=True)
                
                # Remove the plist file
                plist_path.unlink()
                
                self.logger.logger.info("✅ System schedule removed")
                return True
            else:
                self.logger.logger.info("ℹ️ No system schedule found to remove")
                return True
                
        except Exception as e:
            self.logger.log_error(e, "system_schedule_removal")
            return False
    
    def get_next_run_time(self) -> Optional[datetime.datetime]:
        """
        Calculate the next scheduled run time.
        
        Returns:
            Next scheduled run time or None if scheduling is disabled
        """
        if not self.schedule_enabled:
            return None
            
        schedule_config = self.config.get('scheduling', {})
        frequency = schedule_config.get('frequency', 'weekly')
        hour = schedule_config.get('hour', 3)
        minute = schedule_config.get('minute', 30)
        
        now = datetime.datetime.now()
        
        if frequency == 'daily':
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += datetime.timedelta(days=1)
        elif frequency == 'weekly':
            day_of_week = schedule_config.get('day_of_week', 1)  # Monday = 1
            days_ahead = (day_of_week - 1 - now.weekday()) % 7
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            next_run += datetime.timedelta(days=days_ahead)
            if next_run <= now:
                next_run += datetime.timedelta(weeks=1)
        elif frequency == 'monthly':
            # First day of next month
            if now.month == 12:
                next_run = now.replace(year=now.year + 1, month=1, day=1, 
                                     hour=hour, minute=minute, second=0, microsecond=0)
            else:
                next_run = now.replace(month=now.month + 1, day=1, 
                                     hour=hour, minute=minute, second=0, microsecond=0)
        else:
            return None
            
        return next_run
    
    def get_schedule_status(self) -> Dict[str, Any]:
        """
        Get current scheduling status and configuration.
        
        Returns:
            Dictionary with scheduling status information
        """
        next_run = self.get_next_run_time()
        
        return {
            'enabled': self.schedule_enabled,
            'frequency': self.config.get('scheduling', {}).get('frequency', 'weekly'),
            'next_run': next_run.isoformat() if next_run else None,
            'system_configured': self._is_system_configured()
        }
    
    def _is_system_configured(self) -> bool:
        """Check if system-level scheduling is configured"""
        plist_path = Path.home() / "Library/LaunchAgents/com.cleanbook.scheduler.plist"
        return plist_path.exists() 