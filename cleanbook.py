#!/usr/bin/env python3
"""
🧹 CLEANBOOK – Mac Dev Junk Cleaner

A surgical Python utility for Mac users that cleans up development artifacts
from your $HOME directory. Disk space is sacred. Purge the hoard.

Usage:
    python3 cleanbook.py --scan --dry-run
    python3 cleanbook.py --clean --interactive
    python3 cleanbook.py --clean --force --threshold 100MB
    python3 cleanbook.py --schedule weekly
"""

import argparse
import os
import sys
import time
import yaml
from pathlib import Path

# Add utils to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))

import scanner
import nuker
from logger import setup_logger
from scheduler import Scheduler


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        sys.exit(1)


def parse_size_threshold(threshold_str: str) -> float:
    """Parse size threshold string (e.g., '100MB', '1GB') to MB"""
    if not threshold_str:
        return 0.0
    
    threshold_str = threshold_str.upper()
    if threshold_str.endswith('MB'):
        return float(threshold_str[:-2])
    elif threshold_str.endswith('GB'):
        return float(threshold_str[:-2]) * 1024
    elif threshold_str.endswith('KB'):
        return float(threshold_str[:-2]) / 1024
    else:
        # Assume MB if no unit specified
        return float(threshold_str)


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(
        description="🧹 CLEANBOOK – Mac Dev Junk Cleaner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 cleanbook.py --scan --dry-run
  python3 cleanbook.py --clean --interactive
  python3 cleanbook.py --clean --force --threshold 100MB
  python3 cleanbook.py --schedule weekly
        """
    )
    
    # Action arguments
    parser.add_argument('--scan', action='store_true',
                       help='Scan for development artifacts')
    parser.add_argument('--clean', action='store_true',
                       help='Clean up discovered artifacts')
    parser.add_argument('--schedule', choices=['daily', 'weekly', 'monthly'],
                       help='Setup automated scheduling')
    
    # Mode arguments
    parser.add_argument('--dry-run', action='store_true',
                       help='Simulate operations without making changes')
    parser.add_argument('--interactive', action='store_true',
                       help='Prompt for confirmation before each deletion')
    parser.add_argument('--force', action='store_true',
                       help='Force deletion without additional safety checks')
    
    # Configuration arguments
    parser.add_argument('--config', type=Path, default='config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--patterns', type=Path, default='patterns.yaml',
                       help='Path to patterns file')
    parser.add_argument('--target', type=Path, default=Path.home(),
                       help='Target directory to scan/clean')
    parser.add_argument('--threshold', type=str,
                       help='Minimum size threshold for artifacts (e.g., 100MB)')
    
    # Scheduling arguments
    parser.add_argument('--setup-schedule', action='store_true',
                       help='Setup system-level scheduling')
    parser.add_argument('--remove-schedule', action='store_true',
                       help='Remove system-level scheduling')
    parser.add_argument('--schedule-status', action='store_true',
                       help='Show current scheduling status')
    
    # Output arguments
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Suppress non-essential output')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not any([args.scan, args.clean, args.schedule, args.setup_schedule, 
                args.remove_schedule, args.schedule_status]):
        parser.print_help()
        sys.exit(1)
    
    # Load configuration
    config = load_config(args.config)
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else config.get('logging', {}).get('log_level', 'INFO')
    logger = setup_logger(
        log_path=Path(config.get('logging', {}).get('log_path', '~/cleanbook.log')).expanduser(),
        log_level=log_level
    )
    
    logger.logger.info("🧹 CLEANBOOK starting up...")
    
    # Handle scheduling operations
    if args.schedule or args.setup_schedule or args.remove_schedule or args.schedule_status:
        scheduler = Scheduler(args.config, logger)
        
        if args.schedule_status:
            status = scheduler.get_schedule_status()
            print(f"📅 Schedule Status:")
            print(f"   Enabled: {status['enabled']}")
            print(f"   Frequency: {status['frequency']}")
            print(f"   Next Run: {status['next_run']}")
            print(f"   System Configured: {status['system_configured']}")
            return
        
        if args.remove_schedule:
            if scheduler.remove_system_schedule():
                print("✅ System schedule removed successfully")
            else:
                print("❌ Failed to remove system schedule")
                sys.exit(1)
            return
        
        if args.setup_schedule or args.schedule:
            if scheduler.setup_system_schedule():
                print("✅ System schedule configured successfully")
                status = scheduler.get_schedule_status()
                print(f"   Next run: {status['next_run']}")
            else:
                print("❌ Failed to configure system schedule")
                sys.exit(1)
            return
    
    # Validate target directory
    if not args.target.exists():
        logger.logger.error(f"Target directory does not exist: {args.target}")
        sys.exit(1)
    
    # Parse size threshold
    size_threshold = parse_size_threshold(args.threshold or 
                                        config.get('size_thresholds', {}).get('minimum_file_size', '1MB'))
    
    # Initialize scanner
    scanner_instance = scanner.FilesystemScanner(
        patterns_path=args.patterns,
        whitelist=config.get('whitelist_paths', []),
        follow_symlinks=config.get('deletion_behavior', {}).get('follow_symlinks', False),
        parallel_workers=config.get('performance', {}).get('max_workers', 4)
    )
    
    # Initialize nuker
    nuker_instance = nuker.DigitalNuker(
        logger=logger,
        safe_mode=config.get('safe_mode', True),
        parallel_operations=config.get('performance', {}).get('max_workers', 2)
    )
    
    # Perform scan operation
    if args.scan:
        logger.logger.info(f"🔍 Starting scan of: {args.target}")
        logger.log_scan_start(args.target, scanner_instance.patterns)
        
        try:
            artifacts = scanner_instance.scan(args.target, min_size_mb=size_threshold)
            
            if not artifacts:
                print("✨ No artifacts found matching criteria")
                return
            
            # Generate and display report
            report = scanner_instance.generate_report()
            
            print(f"\n📊 SCAN RESULTS")
            print(f"=" * 50)
            print(f"Total artifacts found: {report['summary']['total_artifacts']}")
            print(f"Total size: {report['summary']['total_size_mb']:.2f} MB")
            print(f"Categories: {report['summary']['unique_categories']}")
            
            # Show breakdown by category
            for category, info in report['categories'].items():
                print(f"\n{category.upper()}:")
                print(f"  Count: {info['count']}")
                print(f"  Size: {info['size_mb']:.2f} MB")
            
            # Show top artifacts
            if report['top_artifacts']:
                print(f"\n🏆 TOP ARTIFACTS:")
                for item in report['top_artifacts'][:5]:
                    print(f"  {item['path']} ({item['size_mb']:.2f} MB) [{item['category']}]")
            
            # Save detailed report
            report_path = Path('logs') / f"scan_report_{int(time.time())}.json"
            report_path.parent.mkdir(exist_ok=True)
            
            with open(report_path, 'w') as f:
                import json
                json.dump(report, f, indent=2, default=str)
            
            print(f"\n📝 Detailed report saved to: {report_path}")
            
        except Exception as e:
            logger.log_error(e, "scan_operation")
            print(f"❌ Scan failed: {e}")
            sys.exit(1)
    
    # Perform clean operation
    if args.clean:
        logger.logger.info(f"🧹 Starting cleanup of: {args.target}")
        
        try:
            # First scan to find artifacts
            artifacts = scanner_instance.scan(args.target, min_size_mb=size_threshold)
            
            if not artifacts:
                print("✨ No artifacts found to clean")
                return
            
            print(f"📊 Found {len(artifacts)} artifacts ({sum(a.size_mb for a in artifacts):.2f} MB)")
            
            # Determine deletion mode
            if args.dry_run:
                mode = nuker.DeletionMode.DRY_RUN
                print("👻 DRY RUN MODE - No files will be deleted")
            elif args.interactive:
                mode = nuker.DeletionMode.INTERACTIVE
                print("🤔 INTERACTIVE MODE - Confirmation required for each deletion")
            elif args.force:
                mode = nuker.DeletionMode.FORCE
                print("🔥 FORCE MODE - Proceeding without additional safety checks")
            else:
                mode = nuker.DeletionMode.SAFE
                print("🛡️ SAFE MODE - Using conservative deletion protocols")
            
            # Perform deletion
            results = nuker_instance.delete_artifacts(artifacts, mode=mode)
            
            # Generate summary
            successful = [r for r in results if r.success]
            failed = [r for r in results if not r.success]
            
            total_deleted_size = sum(r.size_mb for r in successful)
            
            print(f"\n🧹 CLEANUP SUMMARY")
            print(f"=" * 50)
            print(f"Successfully deleted: {len(successful)} items ({total_deleted_size:.2f} MB)")
            print(f"Failed deletions: {len(failed)} items")
            
            if failed:
                print(f"\n❌ Failed deletions:")
                for result in failed:
                    print(f"  {result.path}: {result.error}")
            
            # Log summary
            logger.log_summary(
                total_found=len(artifacts),
                total_size_mb=sum(a.size_mb for a in artifacts),
                deleted_count=len(successful),
                deleted_size_mb=total_deleted_size
            )
            
            # Export audit log
            audit_path = logger.export_audit_log()
            print(f"📝 Audit log exported to: {audit_path}")
            
        except Exception as e:
            logger.log_error(e, "cleanup_operation")
            print(f"❌ Cleanup failed: {e}")
            sys.exit(1)
    
    logger.logger.info("✅ CLEANBOOK operation completed successfully")


if __name__ == "__main__":
    main()
