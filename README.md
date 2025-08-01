# 🧹 CLEANBOOK – Mac Dev Junk Cleaner

A surgical Python utility for Mac users that cleans up development artifacts from your `$HOME` directory. Disk space is sacred. Purge the hoard.

## 🚀 Features

- **Intelligent Scanning**: Discovers development artifacts across your filesystem
- **Safe Deletion**: Multiple safety modes with whitelist protection
- **Scheduling**: Automated cleanup with system integration (launchd)
- **Comprehensive Logging**: Forensic audit trail of all operations
- **Parallel Processing**: Multi-threaded scanning for performance
- **Pattern-Based**: Configurable patterns for different development environments

## 📦 Installation

1. Clone the repository:
```bash
git clone https://github.com/geeknik/cleanbook
cd cleanbook
```

2. Create a virtual environment:
```bash
python3.10 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install pyyaml
```

## 🎯 Quick Start

### Scan for artifacts (safe, no changes made):
```bash
python cleanbook.py --scan --dry-run
```

### Interactive cleanup:
```bash
python cleanbook.py --clean --interactive
```

### Force cleanup (use with caution):
```bash
python cleanbook.py --clean --force --threshold 100MB
```

### Setup weekly automated cleanup:
```bash
python cleanbook.py --schedule weekly
```

## 📋 Usage Examples

### Basic Operations

**Scan your home directory for artifacts:**
```bash
python cleanbook.py --scan --target ~
```

**Scan with size threshold:**
```bash
python cleanbook.py --scan --threshold 50MB
```

**Dry run cleanup (simulation only):**
```bash
python cleanbook.py --clean --dry-run
```

**Interactive cleanup with confirmation:**
```bash
python cleanbook.py --clean --interactive
```

### Scheduling

**Check scheduling status:**
```bash
python cleanbook.py --schedule-status
```

**Setup daily automated cleanup:**
```bash
python cleanbook.py --schedule daily
```

**Setup weekly automated cleanup:**
```bash
python cleanbook.py --schedule weekly
```

**Setup monthly automated cleanup:**
```bash
python cleanbook.py --schedule monthly
```

**Remove automated scheduling:**
```bash
python cleanbook.py --remove-schedule
```

### Advanced Options

**Use custom configuration:**
```bash
python cleanbook.py --scan --config custom_config.yaml
```

**Use custom patterns:**
```bash
python cleanbook.py --scan --patterns custom_patterns.yaml
```

**Verbose logging:**
```bash
python cleanbook.py --scan --verbose
```

**Target specific directory:**
```bash
python cleanbook.py --scan --target /path/to/directory
```

## ⚙️ Configuration

### Main Configuration (`config.yaml`)

The main configuration file controls behavior, safety settings, and performance:

```yaml
# Core Behavioral Settings
safe_mode: true                    # Restrict deletions to explicitly matched patterns
aggressive_mode: false             # Include system caches and deeper OS artifacts
interactive_mode: false            # Prompt before each deletion
dry_run_default: true             # Default to simulation mode for safety

# Size Thresholds
size_thresholds:
  minimum_file_size: "1MB"         # Don't delete files smaller than this
  minimum_folder_size: "50MB"      # Focus on directories with significant storage impact

# Whitelist Paths (Protected)
whitelist_paths:
  - /Users/username/Documents      # User documents are sacred
  - /Users/username/Desktop        # Desktop workspace preservation
  - /Users/username/.ssh           # Security credentials must persist

# Logging Configuration
logging:
  enabled: true
  log_path: "~/cleanbook.log"
  log_level: "INFO"                # DEBUG, INFO, WARNING, ERROR

# Scheduling
scheduling:
  enabled: false                   # Disabled by default
  frequency: "weekly"              # weekly, daily, monthly
  hour: 3                          # 3 AM for minimal disruption
  minute: 30
```

### Patterns Configuration (`patterns.yaml`)

Define what constitutes "development artifacts" to clean:

```yaml
python:
  directories:
    - .venv
    - env
    - __pycache__
    - .pytest_cache
  files:
    - "*.pyc"
    - "*.pyo"

javascript:
  directories:
    - node_modules
    - .next
    - dist
    - build
  files:
    - "*.log"
    - npm-debug.log*

rust:
  directories:
    - target
    - .cargo/registry

go:
  directories:
    - vendor
    - .gocache
```

## 🛡️ Safety Features

### Multiple Safety Modes

1. **DRY RUN** (`--dry-run`): Simulate operations without making changes
2. **INTERACTIVE** (`--interactive`): Prompt for confirmation before each deletion
3. **SAFE** (default): Conservative deletion with double-confirmation
4. **FORCE** (`--force`): Proceed without additional safety checks (use with caution)

### Protected Paths

The application automatically protects critical system paths:
- `/System`, `/Library`, `/Applications`
- `/usr`, `/bin`, `/sbin`
- User credentials (`.ssh`, `.gnupg`)
- Keychains and security data

### Whitelist Protection

Configure additional protected paths in `config.yaml`:
```yaml
whitelist_paths:
  - /Users/username/dev/active        # Current development projects
  - /Users/username/Documents         # Important documents
  - /Users/username/.config           # User configuration
```

## 📊 Output and Logging

### Console Output

The application provides clear, emoji-rich output:
```
🧹 CLEANBOOK starting up...
🔍 Starting scan of: /Users/username
📊 SCAN RESULTS
==================================================
Total artifacts found: 156
Total size: 2345.67 MB
Categories: 5

PYTHON.DIRECTORIES:
  Count: 23
  Size: 456.78 MB

JAVASCRIPT.DIRECTORIES:
  Count: 89
  Size: 1234.56 MB

🏆 TOP ARTIFACTS:
  /Users/username/project/node_modules (567.89 MB) [javascript.directories]
  /Users/username/.cache (234.56 MB) [general.directories]
```

### Log Files

- **Main Log**: `~/cleanbook.log` (configurable)
- **Audit Log**: `~/cleanbook.audit.json` (detailed operation history)
- **Scan Reports**: `logs/scan_report_*.json` (detailed scan results)

### Audit Trail

Every operation is logged with timestamps, file sizes, and categories:
```json
{
  "session_id": "2024-01-15T10:30:00",
  "entries": [
    {
      "timestamp": "2024-01-15T10:30:15",
      "action": "discovered",
      "path": "/Users/username/project/node_modules",
      "size_mb": 567.89,
      "category": "javascript.directories"
    },
    {
      "timestamp": "2024-01-15T10:31:00",
      "action": "deleted",
      "path": "/Users/username/project/node_modules",
      "size_mb": 567.89,
      "dry_run": false
    }
  ]
}
```

## 🔧 Advanced Configuration

### Performance Tuning

```yaml
performance:
  parallel_processing: true        # Use multiple threads
  max_workers: 4                   # Number of worker threads
  memory_limit: "1GB"              # Maximum memory usage
  progress_reporting: true         # Show progress during operations
```

### Behavioral Patterns

```yaml
deletion_behavior:
  confirm_before_delete: true       # Require explicit confirmation
  skip_hidden_files: false         # Include dotfiles in analysis
  follow_symlinks: false           # Don't traverse symbolic links
  max_depth: 10                    # Limit recursion depth for safety
  batch_size: 100                  # Process files in batches
```

## 🚨 Safety Warnings

⚠️ **IMPORTANT**: This tool deletes files permanently. Always:

1. **Start with `--dry-run`** to see what would be deleted
2. **Use `--interactive`** mode for first-time use
3. **Review the whitelist** in `config.yaml`
4. **Backup important data** before running cleanup
5. **Test on a small directory first**

## 🐛 Troubleshooting

### Common Issues

**Permission Denied Errors:**
- The application respects file permissions
- Some system directories may be protected
- Check the scan report for permission errors

**No Artifacts Found:**
- Increase the size threshold: `--threshold 1MB`
- Check if target directory is whitelisted
- Verify patterns in `patterns.yaml`

**Scheduling Not Working:**
- Check scheduling status: `--schedule-status`
- Verify launchd permissions
- Check system logs: `launchctl list | grep cleanbook`

### Debug Mode

Enable verbose logging for troubleshooting:
```bash
python cleanbook.py --scan --verbose
```

### Log Analysis

Check the main log file for detailed information:
```bash
tail -f ~/cleanbook.log
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is provided as-is. Use at your own risk. The authors are not responsible for any data loss. Always backup important data before running cleanup operations.

---

**🧹 Keep your development environment clean and your disk space sacred!** 
