# CDS Data Update Scheduling Guide

This document explains how to schedule the CDS data update script to run automatically.

## Script Location

The update script is located at:
```
scripts/update_cds_data.py
```

## Running the Script Manually

### Basic Usage

```bash
# Update using database (production)
python scripts/update_cds_data.py --force-db

# Update using CSV (development)
python scripts/update_cds_data.py --force-csv

# Silent mode (no console output, only logs)
python scripts/update_cds_data.py --force-db --silent
```

### Environment Variables Required

Ensure these variables are set in your `.env` file or environment:

- `DATABASE_URL` - PostgreSQL connection string (for database mode)
- `BETTERSTACK_SOURCE_TOKEN` - BetterStack logging token (optional)
- `BETTERSTACK_INGESTING_HOST` - BetterStack host (optional)
- `ENVIRONMENT` - Set to `production` for database mode

## Scheduling Options

### 1. Linux/Unix Cron

Edit your crontab:
```bash
crontab -e
```

Add one of these lines:

```cron
# Run daily at 12:00 PM UTC (noon)
0 12 * * * cd /path/to/brazillian_cds_datafeeder_v2 && /path/to/python scripts/update_cds_data.py --force-db --silent >> /var/log/cds_update.log 2>&1

# Run every weekday at 9:00 AM UTC
0 9 * * 1-5 cd /path/to/brazillian_cds_datafeeder_v2 && /path/to/python scripts/update_cds_data.py --force-db --silent

# Run every 6 hours
0 */6 * * * cd /path/to/brazillian_cds_datafeeder_v2 && /path/to/python scripts/update_cds_data.py --force-db --silent
```

**Important:** Use absolute paths for Python and the project directory.

### 2. Systemd Timer (Linux)

Create a service file at `/etc/systemd/system/cds-update.service`:

```ini
[Unit]
Description=Brazilian CDS Data Update
After=network.target

[Service]
Type=oneshot
User=your-username
WorkingDirectory=/path/to/brazillian_cds_datafeeder_v2
Environment="PATH=/path/to/python/bin:/usr/bin"
EnvironmentFile=/path/to/brazillian_cds_datafeeder_v2/.env
ExecStart=/path/to/python scripts/update_cds_data.py --force-db --silent
StandardOutput=journal
StandardError=journal
```

Create a timer file at `/etc/systemd/system/cds-update.timer`:

```ini
[Unit]
Description=Run CDS Update Daily
Requires=cds-update.service

[Timer]
# Run daily at 12:00 PM
OnCalendar=*-*-* 12:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start the timer:

```bash
sudo systemctl daemon-reload
sudo systemctl enable cds-update.timer
sudo systemctl start cds-update.timer

# Check status
sudo systemctl status cds-update.timer
sudo systemctl list-timers --all | grep cds
```

### 3. GitHub Actions (CI/CD)

Create `.github/workflows/cds-update.yml`:

```yaml
name: Daily CDS Update

on:
  schedule:
    # Run daily at 12:00 PM UTC
    - cron: '0 12 * * *'
  workflow_dispatch: # Allow manual trigger

jobs:
  update-cds:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run CDS update
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          BETTERSTACK_SOURCE_TOKEN: ${{ secrets.BETTERSTACK_SOURCE_TOKEN }}
          BETTERSTACK_INGESTING_HOST: ${{ secrets.BETTERSTACK_INGESTING_HOST }}
          ENVIRONMENT: production
        run: |
          python scripts/update_cds_data.py --force-db --silent
```

Add these secrets to your GitHub repository:
- `DATABASE_URL`
- `BETTERSTACK_SOURCE_TOKEN`
- `BETTERSTACK_INGESTING_HOST`

### 4. Windows Task Scheduler

1. Open Task Scheduler (`taskschd.msc`)
2. Click "Create Task"
3. **General Tab:**
   - Name: "Brazilian CDS Update"
   - Description: "Daily update of CDS data"
   - Select "Run whether user is logged on or not"
4. **Triggers Tab:**
   - New Trigger
   - Schedule: Daily at 12:00 PM
   - Repeat task every: (optional)
5. **Actions Tab:**
   - New Action
   - Program: `C:\Path\To\Python\python.exe`
   - Arguments: `scripts\update_cds_data.py --force-db --silent`
   - Start in: `C:\Path\To\brazillian_cds_datafeeder_v2`

Or use PowerShell:

```powershell
# Create scheduled task
$action = New-ScheduledTaskAction -Execute 'python.exe' `
    -Argument 'scripts\update_cds_data.py --force-db --silent' `
    -WorkingDirectory 'C:\Path\To\brazillian_cds_datafeeder_v2'

$trigger = New-ScheduledTaskTrigger -Daily -At 12:00PM

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType S4U

Register-ScheduledTask -TaskName "BrazilianCDSUpdate" `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Description "Daily Brazilian CDS data update"
```

### 5. Docker + Cron

If running in Docker, create a `Dockerfile.cron`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Install cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# Add crontab file
COPY crontab /etc/cron.d/cds-update-cron
RUN chmod 0644 /etc/cron.d/cds-update-cron
RUN crontab /etc/cron.d/cds-update-cron

# Create log file
RUN touch /var/log/cron.log

CMD cron && tail -f /var/log/cron.log
```

Create `crontab`:

```cron
0 12 * * * cd /app && python scripts/update_cds_data.py --force-db --silent >> /var/log/cron.log 2>&1
```

Build and run:

```bash
docker build -f Dockerfile.cron -t cds-updater .
docker run -d --env-file .env --name cds-updater cds-updater
```

### 6. Cloud Schedulers

#### AWS EventBridge + Lambda

Create a Lambda function that runs the script and schedule it with EventBridge.

#### Google Cloud Scheduler

Create a Cloud Function and schedule it with Cloud Scheduler.

#### Azure Logic Apps

Create a Logic App with a schedule trigger that calls an Azure Function.

## Monitoring

### Check Last Run

View logs in BetterStack or check the database:

```sql
SELECT * FROM cds_update_history 
ORDER BY update_date DESC 
LIMIT 1;
```

### Script Exit Codes

- `0` - Success
- `1` - Failure

Use exit codes to set up alerts:

```bash
python scripts/update_cds_data.py --force-db --silent
if [ $? -ne 0 ]; then
    echo "CDS update failed!" | mail -s "CDS Update Alert" admin@example.com
fi
```

## Best Practices

1. **Use absolute paths** for Python executable and project directory
2. **Set environment variables** properly (use `.env` file or system environment)
3. **Log output** to a file for debugging
4. **Monitor failures** with alerts
5. **Test manually** before scheduling
6. **Use `--silent` flag** in production to reduce output
7. **Run during off-peak hours** (e.g., overnight or early morning)
8. **Keep time zones in mind** (UTC vs local time)

## Troubleshooting

### Script doesn't run

- Check permissions: `chmod +x scripts/update_cds_data.py`
- Verify Python path: `which python` or `where python`
- Check cron logs: `tail -f /var/log/syslog | grep CRON`
- Test manually first

### Database connection fails

- Verify `DATABASE_URL` is set correctly
- Check network connectivity
- Ensure database is running
- Verify firewall rules allow connection

### No logs appearing

- Check BetterStack configuration
- Verify `BETTERSTACK_SOURCE_TOKEN` is valid
- Check log level: `LOG_LEVEL=INFO` in `.env`
- Look for local logs in terminal output

## Security Notes

⚠️ **Important Security Considerations:**

1. **Never expose cron endpoints via HTTP/REST APIs**
   - Removed from this project for security
   - Prevents unauthorized or accidental execution
   
2. **Protect credentials**
   - Use environment variables, not hardcoded values
   - Use secrets management (GitHub Secrets, AWS Secrets Manager, etc.)
   
3. **Limit permissions**
   - Run scheduled tasks with minimum required permissions
   - Use dedicated service accounts
   
4. **Monitor execution**
   - Set up alerts for failures
   - Review logs regularly
   - Track execution history

## Further Reading

- [Crontab Generator](https://crontab.guru/)
- [Systemd Timers](https://www.freedesktop.org/software/systemd/man/systemd.timer.html)
- [GitHub Actions Scheduling](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule)
- [Task Scheduler PowerShell](https://docs.microsoft.com/en-us/powershell/module/scheduledtasks/)
