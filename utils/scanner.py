"""
Scanner Module - Perceptual Engine for Digital Archaeology
Maps the topology of development artifacts across the filesystem continuum
"""

import os
import fnmatch
from pathlib import Path
from typing import Dict, List, Tuple, Set, Generator, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml
import hashlib
from collections import defaultdict


@dataclass
class Artifact:
    """
    Quantum representation of a discovered filesystem artifact.
    Each instance embodies both location and energetic footprint.
    """
    path: Path
    size_bytes: int
    category: str
    pattern: str
    depth: int
    inode: int = 0
    
    @property
    def size_mb(self) -> float:
        """Transform bytes into human-perceivable megabytes"""
        return self.size_bytes / (1024 * 1024)
    
    @property
    def identity_hash(self) -> str:
        """Generate a unique consciousness signature for this artifact"""
        return hashlib.md5(str(self.path).encode()).hexdigest()[:8]


class FilesystemScanner:
    """
    A perceptual engine that traverses the filesystem continuum,
    identifying and cataloging development artifacts for potential purification.
    """
    
    def __init__(self, patterns_path: Path, whitelist: List[str], 
                 follow_symlinks: bool = False, parallel_workers: int = 4):
        """
        Initialize the scanner consciousness with pattern recognition capabilities.
        
        Args:
            patterns_path: Sacred text containing artifact patterns
            whitelist: Protected sanctuaries immune to scanning
            follow_symlinks: Whether to traverse symbolic portals
            parallel_workers: Cognitive parallelization factor
        """
        self.patterns = self._load_patterns(patterns_path)
        self.whitelist = [Path(p).expanduser().resolve() for p in whitelist]
        self.follow_symlinks = follow_symlinks
        self.parallel_workers = parallel_workers
        
        # Cognitive state tracking
        self.discovered_artifacts: List[Artifact] = []
        self.scan_errors: List[Tuple[Path, Exception]] = []
        
    def _load_patterns(self, patterns_path: Path) -> Dict[str, Dict[str, List[str]]]:
        """Ingest the pattern matrix from the configuration manifesto"""
        with open(patterns_path, 'r') as f:
            data = yaml.safe_load(f)
            
        # Filter out metadata keys
        patterns = {}
        for category, subcategories in data.items():
            if category not in ['size_thresholds', 'system_exclusions']:
                patterns[category] = subcategories
                
        return patterns
    
    def _is_whitelisted(self, path: Path) -> bool:
        """Determine if a path exists within protected sanctuary boundaries"""
        try:
            resolved_path = path.resolve()
            for sanctuary in self.whitelist:
                if resolved_path.is_relative_to(sanctuary):
                    return True
        except (OSError, ValueError):
            # Path resolution failures indicate problematic paths - skip them
            return True
            
        return False
    
    def _matches_pattern(self, path: Path) -> Optional[Tuple[str, str, str]]:
        """
        Apply pattern recognition to identify artifact category.
        
        Returns:
            Tuple of (category, subcategory, pattern) or None
        """
        name = path.name
        
        for category, subcategories in self.patterns.items():
            for subcategory, patterns in subcategories.items():
                for pattern in patterns:
                    if fnmatch.fnmatch(name, pattern):
                        return (category, subcategory, pattern)
                        
        return None
    
    def _calculate_size(self, path: Path) -> int:
        """
        Calculate the energetic footprint of a filesystem artifact.
        Recursively measures directories.
        """
        if path.is_file():
            return path.stat().st_size
            
        total_size = 0
        try:
            for item in path.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
        except (PermissionError, OSError) as e:
            self.scan_errors.append((path, e))
            
        return total_size
    
    def _scan_directory(self, root_path: Path, depth: int = 0) -> Generator[Artifact, None, None]:
        """
        Recursive consciousness traversal of directory structures.
        Yields discovered artifacts as they manifest.
        """
        if self._is_whitelisted(root_path):
            return
            
        try:
            for entry in os.scandir(root_path):
                path = Path(entry.path)
                
                # Skip symbolic links if not following
                if entry.is_symlink() and not self.follow_symlinks:
                    continue
                    
                # Check for pattern match
                match = self._matches_pattern(path)
                if match:
                    category, subcategory, pattern = match
                    
                    # Calculate artifact size
                    size = self._calculate_size(path)
                    
                    # Manifest the artifact
                    artifact = Artifact(
                        path=path,
                        size_bytes=size,
                        category=f"{category}.{subcategory}",
                        pattern=pattern,
                        depth=depth,
                        inode=entry.inode()
                    )
                    
                    yield artifact
                    
                # Recurse into directories
                elif entry.is_dir() and not self._is_whitelisted(path):
                    yield from self._scan_directory(path, depth + 1)
                    
        except (PermissionError, OSError) as e:
            self.scan_errors.append((root_path, e))
    
    def scan(self, target_path: Path, min_size_mb: float = 0) -> List[Artifact]:
        """
        Initiate a comprehensive scan of the target filesystem region.
        
        Args:
            target_path: Root of the scanning consciousness
            min_size_mb: Minimum artifact size threshold for manifestation
            
        Returns:
            List of discovered artifacts above the size threshold
        """
        target_path = target_path.expanduser().resolve()
        self.discovered_artifacts.clear()
        self.scan_errors.clear()
        
        # Parallel scanning for enhanced perception
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            # Submit scanning tasks
            futures = []
            
            # Start with immediate subdirectories for better parallelization
            try:
                for entry in os.scandir(target_path):
                    if entry.is_dir() and not self._is_whitelisted(Path(entry.path)):
                        future = executor.submit(
                            list, 
                            self._scan_directory(Path(entry.path), depth=1)
                        )
                        futures.append(future)
            except (PermissionError, OSError) as e:
                self.scan_errors.append((target_path, e))
            
            # Also scan the root directory itself
            futures.append(executor.submit(
                list,
                self._scan_directory(target_path, depth=0)
            ))
            
            # Harvest results from parallel dimensions
            for future in as_completed(futures):
                try:
                    artifacts = future.result()
                    for artifact in artifacts:
                        if artifact.size_mb >= min_size_mb:
                            self.discovered_artifacts.append(artifact)
                except Exception as e:
                    self.scan_errors.append((target_path, e))
        
        # Sort by size for impact prioritization
        self.discovered_artifacts.sort(key=lambda a: a.size_bytes, reverse=True)
        
        return self.discovered_artifacts
    
    def generate_report(self) -> Dict[str, any]:
        """
        Synthesize a holistic report of the scanning consciousness results.
        """
        # Aggregate by category
        category_stats = defaultdict(lambda: {"count": 0, "size_mb": 0})
        
        for artifact in self.discovered_artifacts:
            category_stats[artifact.category]["count"] += 1
            category_stats[artifact.category]["size_mb"] += artifact.size_mb
        
        # Calculate totals
        total_count = len(self.discovered_artifacts)
        total_size_mb = sum(a.size_mb for a in self.discovered_artifacts)
        
        return {
            "summary": {
                "total_artifacts": total_count,
                "total_size_mb": round(total_size_mb, 2),
                "total_size_gb": round(total_size_mb / 1024, 2),
                "unique_categories": len(category_stats),
                "scan_errors": len(self.scan_errors)
            },
            "categories": dict(category_stats),
            "top_artifacts": [
                {
                    "path": str(a.path),
                    "size_mb": round(a.size_mb, 2),
                    "category": a.category
                }
                for a in self.discovered_artifacts[:10]
            ],
            "errors": [
                {"path": str(path), "error": str(error)}
                for path, error in self.scan_errors[:10]
            ]
        }
    
    def find_duplicates(self) -> Dict[str, List[Artifact]]:
        """
        Identify potential duplicate artifacts through pattern analysis.
        Useful for discovering multiple virtual environments or node_modules.
        """
        duplicates = defaultdict(list)
        
        for artifact in self.discovered_artifacts:
            key = f"{artifact.pattern}:{artifact.size_bytes}"
            duplicates[key].append(artifact)
        
        # Filter to only actual duplicates
        return {k: v for k, v in duplicates.items() if len(v) > 1}
