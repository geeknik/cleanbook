"""
Logger Module - Forensic Consciousness for Digital Purification
A temporal audit trail mapping the archaeology of destruction
"""

import os
import sys
import logging
import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json
from enum import Enum, auto


def setup_logger(log_path: Optional[Path] = None, log_level: str = "INFO") -> 'CleanBookLogger':
    """
    Factory function to create and configure a CleanBookLogger instance.
    
    Args:
        log_path: Path for log file storage
        log_level: Logging verbosity level
        
    Returns:
        Configured CleanBookLogger instance
    """
    return CleanBookLogger(log_path, log_level)


class LogLevel(Enum):
    """Consciousness states of the logging mechanism"""
    DEBUG = auto()    # Quantum-level observations
    INFO = auto()     # Normative operational awareness
    WARNING = auto()  # Anomaly detection signals
    ERROR = auto()    # System perturbation events
    CRITICAL = auto() # Existential threat markers


class CleanBookLogger:
    """
    A forensic consciousness that chronicles the digital purification process.
    Each log entry represents a moment in the temporal flow of disk space liberation.
    """
    
    def __init__(self, log_path: Optional[Path] = None, log_level: str = "INFO"):
        """
        Initialize the logging consciousness with configurable verbosity.
        
        Args:
            log_path: Sacred path for log manifestation
            log_level: Threshold for consciousness activation
        """
        self.log_path = log_path or Path.home() / "cleanbook.log"
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Ensure log directory exists in the filesystem continuum
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure the root logger with our consciousness parameters
        self._configure_logger()
        
        # Audit log for forensic analysis
        self.audit_log = []
        
    def _configure_logger(self):
        """Configure the logging mechanism with appropriate formatters and handlers"""
        # Create formatter - timestamp as consciousness marker
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler for persistent consciousness
        file_handler = logging.FileHandler(self.log_path, mode='a', encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(self.log_level)
        
        # Console handler for real-time awareness
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(self.log_level)
        
        # Configure root logger
        logger = logging.getLogger('cleanbook')
        logger.setLevel(self.log_level)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # Prevent propagation to avoid duplicate logs
        logger.propagate = False
        
        self.logger = logger
        
    def log_scan_start(self, target_path: Path, patterns: Dict[str, Any]):
        """Chronicle the initiation of a scanning ritual"""
        self.logger.info(f"🔍 Initiating scan consciousness at: {target_path}")
        self.logger.debug(f"Pattern matrix loaded: {len(patterns)} categories")
        
    def log_artifact_found(self, path: Path, size_mb: float, category: str):
        """Record the discovery of a digital artifact"""
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": "discovered",
            "path": str(path),
            "size_mb": round(size_mb, 2),
            "category": category
        }
        self.audit_log.append(entry)
        self.logger.info(f"📁 Found {category} artifact: {path} ({size_mb:.2f} MB)")
        
    def log_deletion(self, path: Path, size_mb: float, dry_run: bool = False):
        """Chronicle the destruction (or simulated destruction) of an artifact"""
        action = "simulated_deletion" if dry_run else "deleted"
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action,
            "path": str(path),
            "size_mb": round(size_mb, 2),
            "dry_run": dry_run
        }
        self.audit_log.append(entry)
        
        icon = "🔥" if not dry_run else "👻"
        self.logger.info(f"{icon} {action.title()}: {path} ({size_mb:.2f} MB)")
        
    def log_whitelist_skip(self, path: Path):
        """Record preservation of whitelisted sanctuaries"""
        self.logger.debug(f"⛔ Whitelist protection: {path}")
        
    def log_error(self, error: Exception, context: str):
        """Chronicle system perturbations and anomalies"""
        self.logger.error(f"❌ Error in {context}: {type(error).__name__}: {str(error)}")
        
    def log_summary(self, total_found: int, total_size_mb: float, 
                    deleted_count: int, deleted_size_mb: float):
        """Generate a holistic summary of the purification session"""
        self.logger.info("="*60)
        self.logger.info("🧹 CLEANBOOK SESSION SUMMARY")
        self.logger.info(f"📊 Total artifacts discovered: {total_found} ({total_size_mb:.2f} MB)")
        self.logger.info(f"🔥 Total artifacts purged: {deleted_count} ({deleted_size_mb:.2f} MB)")
        self.logger.info(f"💾 Disk space liberated: {deleted_size_mb:.2f} MB")
        self.logger.info("="*60)
        
    def export_audit_log(self, export_path: Optional[Path] = None) -> Path:
        """
        Export the audit log for forensic analysis.
        
        Returns:
            Path to the exported audit log
        """
        export_path = export_path or self.log_path.with_suffix('.audit.json')
        
        with open(export_path, 'w') as f:
            json.dump({
                "session_id": datetime.datetime.now().isoformat(),
                "entries": self.audit_log,
                "summary": {
                    "total_entries": len(self.audit_log),
                    "deletions": sum(1 for e in self.audit_log if e.get("action") == "deleted"),
                    "discoveries": sum(1 for e in self.audit_log if e.get("action") == "discovered")
                }
            }, f, indent=2)
            
        self.logger.info(f"📝 Audit log exported to: {export_path}")
        return export_path
        
    def rotate_logs(self, retention_days: int = 30):
        """Implement temporal decay for log artifacts"""
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=retention_days)
        
        # Archive old logs
        if self.log_path.exists():
            archive_path = self.log_path.with_suffix(f'.{cutoff_date.strftime("%Y%m%d")}.log')
            if self.log_path.stat().st_mtime < cutoff_date.timestamp():
                self.log_path.rename(archive_path)
                self.logger.info(f"📦 Archived old log to: {archive_path}")
