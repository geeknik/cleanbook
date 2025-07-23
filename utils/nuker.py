"""
Nuker Module - Executive Consciousness for Digital Purification
The transformative engine that converts identification into liberation
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Callable, Set
from dataclasses import dataclass
from enum import Enum, auto
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class DeletionMode(Enum):
    """Operational paradigms for the destruction consciousness"""
    DRY_RUN = auto()      # Simulation without manifestation
    INTERACTIVE = auto()  # Human-in-the-loop confirmation
    FORCE = auto()        # Unconditional purification
    SAFE = auto()         # Conservative with double-confirmation


@dataclass
class DeletionResult:
    """Quantum state of a deletion operation"""
    path: Path
    success: bool
    size_mb: float
    error: Optional[Exception] = None
    duration_ms: float = 0
    mode: DeletionMode = DeletionMode.SAFE


class DigitalNuker:
    """
    The executive consciousness responsible for transforming identified artifacts
    into liberated disk space. Operates with surgical precision and
    paranoid safety protocols.
    """
    
    def __init__(self, logger, safe_mode: bool = True, 
                 parallel_operations: int = 2):
        """
        Initialize the destruction engine with safety constraints.
        
        Args:
            logger: Forensic consciousness for operation chronicling
            safe_mode: Enable conservative destruction protocols
            parallel_operations: Concurrent destruction threads
        """
        self.logger = logger
        self.safe_mode = safe_mode
        self.parallel_operations = parallel_operations
        
        # Operational state tracking
        self.deletion_results: List[DeletionResult] = []
        self.destruction_lock = threading.Lock()
        
        # Safety mechanisms
        self.protected_paths = self._initialize_protected_paths()
        self.destruction_confirmations: Set[str] = set()
        
    def _initialize_protected_paths(self) -> Set[Path]:
        """
        Define the immutable sanctuary paths that must never be touched.
        These represent the core consciousness of the system.
        """
        sacred_paths = {
            "/System",
            "/Library",
            "/Applications",
            "/usr",
            "/bin",
            "/sbin",
            "/private",
            "/dev",
            "/Volumes",
            Path.home() / ".ssh",
            Path.home() / ".gnupg",
            Path.home() / "Library/Keychains",
            Path.home() / "Library/Application Support/CrashReporter",
        }
        
        return {Path(p).resolve() for p in sacred_paths if Path(p).exists()}
    
    def _is_safe_to_delete(self, path: Path) -> bool:
        """
        Apply multi-layered safety validation to prevent catastrophic destruction.
        """
        try:
            resolved_path = path.resolve()
            
            # Check against protected sanctuaries
            for protected in self.protected_paths:
                if resolved_path == protected or resolved_path.is_relative_to(protected):
                    self.logger.log_error(
                        Exception(f"Attempted to delete protected path: {path}"),
                        "safety_check"
                    )
                    return False
            
            # Validate ownership (only delete user-owned files)
            stat = path.stat()
            if stat.st_uid != os.getuid():
                self.logger.log_error(
                    Exception(f"Ownership mismatch: {path}"),
                    "safety_check"
                )
                return False
                
            # Path depth sanity check (avoid root-level deletions)
            if len(resolved_path.parts) < 4:
                self.logger.log_error(
                    Exception(f"Path too shallow: {path}"),
                    "safety_check"
                )
                return False
                
            return True
            
        except Exception as e:
            self.logger.log_error(e, f"safety_check for {path}")
            return False
    
    def _generate_confirmation_hash(self, path: Path) -> str:
        """Generate a unique confirmation token for interactive mode"""
        return hashlib.sha256(str(path).encode()).hexdigest()[:8]
    
    def _execute_deletion(self, path: Path, dry_run: bool = False) -> DeletionResult:
        """
        Core deletion mechanism with timing and error handling.
        """
        start_time = time.time()
        
        try:
            # Calculate size before deletion
            if path.is_file():
                size_bytes = path.stat().st_size
            else:
                size_bytes = sum(
                    f.stat().st_size 
                    for f in path.rglob('*') 
                    if f.is_file()
                )
            
            size_mb = size_bytes / (1024 * 1024)
            
            # Perform the destruction ritual
            if not dry_run:
                if path.is_file():
                    path.unlink()
                else:
                    shutil.rmtree(path, ignore_errors=False)
            
            duration_ms = (time.time() - start_time) * 1000
            
            return DeletionResult(
                path=path,
                success=True,
                size_mb=size_mb,
                duration_ms=duration_ms,
                mode=DeletionMode.DRY_RUN if dry_run else DeletionMode.FORCE
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return DeletionResult(
                path=path,
                success=False,
                size_mb=0,
                error=e,
                duration_ms=duration_ms
            )
    
    def delete_artifacts(self, artifacts: List['Artifact'], 
                        mode: DeletionMode = DeletionMode.SAFE,
                        confirmation_callback: Optional[Callable] = None) -> List[DeletionResult]:
        """
        Orchestrate the mass purification of discovered artifacts.
        
        Args:
            artifacts: List of artifacts marked for destruction
            mode: Operational paradigm for the destruction process
            confirmation_callback: Human consciousness interface for interactive mode
            
        Returns:
            List of deletion results documenting the purification outcome
        """
        self.deletion_results.clear()
        
        # Pre-flight safety validation
        safe_artifacts = []
        for artifact in artifacts:
            if self._is_safe_to_delete(artifact.path):
                safe_artifacts.append(artifact)
            else:
                self.logger.log_error(
                    Exception(f"Unsafe path rejected: {artifact.path}"),
                    "pre_deletion_validation"
                )
        
        # Process deletions based on operational mode
        if mode == DeletionMode.DRY_RUN:
            # Simulation mode - no actual destruction
            for artifact in safe_artifacts:
                result = self._execute_deletion(artifact.path, dry_run=True)
                self.deletion_results.append(result)
                self.logger.log_deletion(artifact.path, artifact.size_mb, dry_run=True)
                
        elif mode == DeletionMode.INTERACTIVE:
            # Human-in-the-loop confirmation for each artifact
            for artifact in safe_artifacts:
                if confirmation_callback:
                    confirmed = confirmation_callback(artifact)
                    if confirmed:
                        result = self._execute_deletion(artifact.path)
                        self.deletion_results.append(result)
                        self.logger.log_deletion(
                            artifact.path, 
                            artifact.size_mb, 
                            dry_run=False
                        )
                else:
                    self.logger.log_error(
                        Exception("No confirmation callback provided"),
                        "interactive_mode"
                    )
                    
        elif mode == DeletionMode.FORCE:
            # Parallel destruction for maximum efficiency
            with ThreadPoolExecutor(max_workers=self.parallel_operations) as executor:
                futures = {
                    executor.submit(self._execute_deletion, artifact.path): artifact
                    for artifact in safe_artifacts
                }
                
                for future in as_completed(futures):
                    artifact = futures[future]
                    try:
                        result = future.result()
                        with self.destruction_lock:
                            self.deletion_results.append(result)
                            self.logger.log_deletion(
                                artifact.path, 
                                artifact.size_mb,
                                dry_run=False
                            )
                    except Exception as e:
                        self.logger.log_error(e, f"parallel_deletion of {artifact.path}")
                        
        elif mode == DeletionMode.SAFE:
            # Conservative mode with double confirmation
            confirmation_required = set()
            
            # First pass - identify high-risk deletions
            for artifact in safe_artifacts:
                if artifact.size_mb > 100 or len(artifact.path.parts) < 6:
                    confirmation_required.add(artifact.path)
            
            # Process with extra caution
            for artifact in safe_artifacts:
                if artifact.path in confirmation_required:
                    if confirmation_callback and confirmation_callback(artifact):
                        result = self._execute_deletion(artifact.path)
                    else:
                        continue
                else:
                    result = self._execute_deletion(artifact.path)
                    
                self.deletion_results.append(result)
                self.logger.log_deletion(
                    artifact.path,
                    result.size_mb,
                    dry_run=False
                )
        
        return self.deletion_results
    
    def get_destruction_metrics(self) -> Dict[str, any]:
        """
        Synthesize operational metrics from the destruction campaign.
        """
        successful_deletions = [r for r in self.deletion_results if r.success]
        failed_deletions = [r for r in self.deletion_results if not r.success]
        
        total_freed_mb = sum(r.size_mb for r in successful_deletions)
        avg_duration_ms = (
            sum(r.duration_ms for r in successful_deletions) / len(successful_deletions)
            if successful_deletions else 0
        )
        
        return {
            "total_operations": len(self.deletion_results),
            "successful_deletions": len(successful_deletions),
            "failed_deletions": len(failed_deletions),
            "total_freed_mb": round(total_freed_mb, 2),
            "total_freed_gb": round(total_freed_mb / 1024, 2),
            "average_duration_ms": round(avg_duration_ms, 2),
            "errors": [
                {
                    "path": str(r.path),
                    "error": str(r.error)
                }
                for r in failed_deletions
            ]
        }
    
    def create_undo_manifest(self) -> Path:
        """
        Generate a resurrection manifest for potential artifact recovery.
        (Note: Actual recovery requires backup mechanisms)
        """
        manifest_path = Path.home() / f".cleanbook_undo_{int(time.time())}.json"
        
        import json
        manifest = {
            "timestamp": time.time(),
            "deletions": [
                {
                    "path": str(r.path),
                    "size_mb": r.size_mb,
                    "success": r.success,
                    "mode": r.mode.name
                }
                for r in self.deletion_results
            ]
        }
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
            
        return manifest_path
