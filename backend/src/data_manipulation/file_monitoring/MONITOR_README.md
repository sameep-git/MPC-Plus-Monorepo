# MPC-Plus Folder Monitor

An automated background service that monitors the 'iDrive' folder for new data uploads and processes them using the MPC-Plus DataProcessor.

## Overview

This system provides:
- **Automatic folder monitoring** - Watches the 'iDrive' folder for new uploads
- **Background processing** - Runs continuously in the background
- **Data processing integration** - Automatically calls the DataProcessor when new folders are detected
- **Comprehensive logging** - Tracks all operations with detailed logs
- **Error handling** - Robust error handling and recovery

## Quick Start

### 1. Setup (First Time Only)

Run the setup command to install dependencies and create necessary folders:

```bash
python -m src.data_manipulation.file_monitoring.main setup
```

### 2. Start Monitoring

**Simple start (interactive mode) - only processes NEW folders:**
```bash
python -m src.data_manipulation.file_monitoring.main start
```

**Start and scan existing folders on startup:**
```bash
python -m src.data_manipulation.file_monitoring.main start --scan-existing
```

**Background service mode:**
```bash
python -m src.data_manipulation.file_monitoring.main start --background
```


### 3. Using the System

1. The monitor creates an 'iDrive' folder if it doesn't exist
2. Upload/copy new data folders into the 'iDrive' directory
3. The monitor automatically detects new folders and processes them
4. Processing results are logged to `folder_monitor.log`


## Commands

### Main Entry Point (`src/data_manipulation/file_monitoring/main.py`)

```bash
# System setup
python -m src.data_manipulation.file_monitoring.main setup

# Start monitoring (interactive) - only processes NEW folders added while running
python -m src.data_manipulation.file_monitoring.main start

# Start monitoring and scan existing folders on startup
python -m src.data_manipulation.file_monitoring.main start --scan-existing

# Start monitoring custom folder
python -m src.data_manipulation.file_monitoring.main start --path /path/to/custom/folder

# Start in background mode
python -m src.data_manipulation.file_monitoring.main start --background

# Check service status
python -m src.data_manipulation.file_monitoring.main status

# Enable verbose logging
python -m src.data_manipulation.file_monitoring.main start --verbose
```

### Service Runner (`src/data_manipulation/file_monitoring/run_monitor_service.py`)

```bash
# Install dependencies only
python -m src.data_manipulation.file_monitoring.run_monitor_service install-deps

# Start service
python -m src.data_manipulation.file_monitoring.run_monitor_service start

# Check status
python -m src.data_manipulation.file_monitoring.run_monitor_service status
```

## How It Works

1. **Folder Monitoring**: Uses the `watchdog` library to monitor filesystem events
2. **Event Detection**: Detects when new folders are created or moved into iDrive
3. **Startup Behavior**: 
   - By default, only processes NEW folders added while the monitor is running
   - Use `--scan-existing` flag to process existing folders on startup
4. **Readiness Check**: Verifies that uploads are complete (checks for Results.csv)
5. **Data Processing**: Creates a DataProcessor instance and calls its Run() method
6. **Beam Detection**: The DataProcessor automatically detects beam types (6e, 15x, etc.)
7. **Logging**: All operations are logged with timestamps and details

## Supported Beam Types

The system currently supports:
- **6e beams** - Processed using EBeamModel
- **15x beams** - Processed using XBeamModel

Detection is based on the folder path containing these identifiers.

## Configuration

### Database Connection
The system uses PostgreSQL for data storage. Configure connection parameters in your `.env` file:

```
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=your_database_name
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password_here
```

Alternatively, you can use a connection string:
```
POSTGRES_CONNECTION_STRING=postgresql://your_username:your_password_here@localhost:5432/your_database_name
```

### Monitored Folder
Default: `iDrive` (in project root)
Can be changed using the `--path` argument.

### Log Files
- Monitor logs: `logs/folder_monitor.log`
- Service logs: Console output (captured when using service runner)

### Dependencies
- Python 3.7+
- watchdog 3.0.0 (for filesystem monitoring)
- psycopg2-binary (for PostgreSQL connectivity)

## Troubleshooting

### Common Issues

**"Python not found"**
- Ensure Python 3.7+ is installed and in your system PATH
- Try `python3` instead of `python` on some systems

**"Module not found" errors**
- Run `python -m src.data_manipulation.file_monitoring.main setup` to install dependencies
- Ensure you're running from the project root directory

**"iDrive folder not found"**
- The folder is created automatically on first run
- Check permissions if creation fails

**Files not being processed**
- Ensure folders contain a `Results.csv` file
- Check the log file for specific error messages
- Verify the folder path matches expected beam type patterns

### Log Analysis

Check `folder_monitor.log` for:
- Folder detection events
- Processing status
- Error messages and stack traces
- Performance information

## Development

### Adding New Beam Types

To add support for new beam types:

1. Create a new model class in `src/data_manipulation/models/`
2. Add detection logic in `DataProcessor.Run()`
3. Implement extraction logic in `Extractor` class

### Customizing Monitoring

The monitoring behavior can be customized by:
- Modifying `iDriveFolderHandler` class in `folder_monitor.py`
- Adjusting the readiness check logic in `_is_folder_ready()`
- Adding new event types in the event handler methods

## Security Notes

- The monitor only processes folders in the designated iDrive directory
- No network connections are made by the monitoring service
- All file operations are logged for audit purposes
- The service runs with the permissions of the user who starts it

## Support

For issues or questions:
1. Check the log files for error details
2. Verify system requirements are met
3. Ensure proper file permissions
4. Review this documentation for configuration options
