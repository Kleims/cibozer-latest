# Cibozer Server Management Guide

## Quick Start

### Starting the Server

**Option 1: Python Script (Recommended)**
```bash
python run_server.py
```

**Option 2: Batch File (Windows)**
```bash
start_dev.bat
```

**Option 3: Direct Python**
```bash
python app.py
```

### Stopping the Server

**Option 1: Keyboard Interrupt**
Press `Ctrl+C` in the terminal where the server is running

**Option 2: Batch File (Windows)**
```bash
stop_dev.bat
```

**Option 3: Python Script**
```bash
python dev_server.py stop
```

## Server Details

- **Default Port**: 5001
- **Auto Port Selection**: If 5001 is busy, automatically finds next available port
- **URLs**:
  - Main App: http://localhost:5001
  - Admin Panel: http://localhost:5001/admin
  - Health Check: http://localhost:5001/health
  - API Metrics: http://localhost:5001/metrics

## Admin Access

```
Username: admin
Password: (--F#.A8xzYlTn/3
```

## Common Issues & Solutions

### Issue: "Port already in use"

**Solution 1**: The server will automatically find another port
**Solution 2**: Kill all Python processes:
```bash
# Windows
stop_dev.bat

# Or manually
wmic process where "name='python.exe' and commandline like '%app.py%'" delete
```

### Issue: "Log file permission error"

**Solution**: This has been fixed. Old log files are automatically rotated on startup.

### Issue: "Module not found"

**Solution**: Install missing dependencies:
```bash
pip install -r requirements.txt
pip install psutil  # For process management
```

## Development Features

- **Auto-reload**: Disabled by default to prevent double startup
- **Debug Mode**: Enabled in development for detailed error messages
- **Threading**: Enabled for better performance
- **Logging**: Check `logs/` folder for application logs

## Process Management

### Check if server is running
```bash
python dev_server.py status
```

### Restart server
```bash
python dev_server.py restart
```

### Clean shutdown
The server handles Ctrl+C gracefully and cleans up resources.

## Best Practices

1. **Always use the provided scripts** instead of running `python app.py` directly
2. **Check the console output** for the actual port if 5001 is busy
3. **Monitor logs** in the `logs/` directory for errors
4. **Use clean shutdown** (Ctrl+C) to prevent port blocking issues

## Environment Variables

The server automatically sets:
- `FLASK_ENV=development`
- `DEBUG=True`

For production, use:
- `FLASK_ENV=production`
- `DEBUG=False`

## Troubleshooting Commands

```bash
# Check what's using a port
netstat -ano | findstr :5001

# List all Python processes
wmic process where "name='python.exe'" get processid,commandline

# Kill specific process
wmic process where "ProcessId=12345" delete

# Clean start (Windows)
stop_dev.bat && timeout /t 2 && start_dev.bat
```

## Next Steps

After starting the server:
1. Visit http://localhost:5001 to see the main app
2. Login to admin panel at http://localhost:5001/admin
3. Create a test user account
4. Try generating meal plans
5. Test the payment flow (currently in test mode)

---

Generated: 2025-01-17
Version: 1.0.0