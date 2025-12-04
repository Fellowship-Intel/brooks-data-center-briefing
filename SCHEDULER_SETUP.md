# Cloud Scheduler Setup for Daily Watchlist Reports

This guide explains how to set up Cloud Scheduler to automatically generate daily watchlist reports at 3:00 AM PST/PDT.

## Overview

Cloud Scheduler will trigger the API endpoint `/reports/generate/watchlist` daily at 3:00 AM America/Los_Angeles timezone.

## Prerequisites

1. **API Service Deployed**: The `brooks-briefing-api` Cloud Run service must be deployed
2. **Cloud Scheduler API Enabled**: Enable the Cloud Scheduler API in your GCP project
3. **Service Account Permissions**: A service account with Cloud Run Invoker role

## Quick Setup

### Automated Setup (Recommended)

```bash
# Bash
./scripts/setup_scheduler.sh

# PowerShell
.\scripts\setup_scheduler.ps1
```

The script will:
- Detect your API service URL
- Create a service account if needed
- Grant necessary permissions
- Create or update the Cloud Scheduler job

### Manual Setup

If you prefer to set it up manually:

```bash
# 1. Get your API service URL
API_URL=$(gcloud run services describe brooks-briefing-api \
  --region us-central1 --format 'value(status.url)')

# 2. Create service account (if needed)
gcloud iam service-accounts create cloud-scheduler-sa \
  --display-name="Cloud Scheduler Service Account" \
  --project mikebrooks

# 3. Grant Cloud Run Invoker role
gcloud run services add-iam-policy-binding brooks-briefing-api \
  --region us-central1 \
  --member="serviceAccount:cloud-scheduler-sa@mikebrooks.iam.gserviceaccount.com" \
  --role="roles/run.invoker"

# 4. Create the scheduler job
gcloud scheduler jobs create http brooks-daily-watchlist \
  --location=us-central1 \
  --schedule="0 3 * * *" \
  --time-zone="America/Los_Angeles" \
  --uri="${API_URL}/reports/generate/watchlist" \
  --http-method=POST \
  --oidc-service-account-email="cloud-scheduler-sa@mikebrooks.iam.gserviceaccount.com" \
  --oidc-token-audience="${API_URL}" \
  --headers="Content-Type=application/json" \
  --message-body='{"client_id":"michael_brooks","watchlist":["IREN","CRWV","NBIS","MRVL"]}'
```

## Configuration

### Schedule

- **Cron Expression**: `0 3 * * *` (3:00 AM daily)
- **Time Zone**: `America/Los_Angeles` (automatically handles PST/PDT)

### Endpoint

- **URL**: `https://brooks-briefing-api-XXXXX-uc.a.run.app/reports/generate/watchlist`
- **Method**: `POST`
- **Content-Type**: `application/json`

### Request Body

```json
{
  "client_id": "michael_brooks",
  "watchlist": ["IREN", "CRWV", "NBIS", "MRVL"]
}
```

### Authentication

The scheduler uses OIDC authentication with a service account:
- **Service Account**: `cloud-scheduler-sa@PROJECT_ID.iam.gserviceaccount.com`
- **Role**: `roles/run.invoker` (allows invoking Cloud Run services)

## Testing

### Test the Job Manually

```bash
# Bash
./scripts/test_scheduler_job.sh

# PowerShell
.\scripts\test_scheduler_job.ps1

# Or manually
gcloud scheduler jobs run brooks-daily-watchlist --location us-central1
```

### Verify Execution

After triggering the job:

1. **Check Scheduler Job Status**:
   ```bash
   gcloud scheduler jobs describe brooks-daily-watchlist --location us-central1
   ```

2. **Check Cloud Run Logs**:
   ```bash
   gcloud logs read \
     --project=mikebrooks \
     --region=us-central1 \
     --service=brooks-briefing-api \
     --limit=50
   ```

3. **Check Firestore**:
   - Verify a new report document was created for today's date
   - Check the `daily_reports` collection in Firestore

## Management Commands

### View Job Details

```bash
gcloud scheduler jobs describe brooks-daily-watchlist --location us-central1
```

### List All Jobs

```bash
gcloud scheduler jobs list --location us-central1
```

### Pause Job

```bash
gcloud scheduler jobs pause brooks-daily-watchlist --location us-central1
```

### Resume Job

```bash
gcloud scheduler jobs resume brooks-daily-watchlist --location us-central1
```

### Update Job

```bash
# Update schedule
gcloud scheduler jobs update http brooks-daily-watchlist \
  --location us-central1 \
  --schedule="0 4 * * *"  # Change to 4:00 AM

# Update request body
gcloud scheduler jobs update http brooks-daily-watchlist \
  --location us-central1 \
  --message-body='{"client_id":"michael_brooks","watchlist":["IREN","CRWV"]}'
```

### Delete Job

```bash
gcloud scheduler jobs delete brooks-daily-watchlist --location us-central1
```

## Troubleshooting

### Job Not Running

1. **Check Job State**:
   ```bash
   gcloud scheduler jobs describe brooks-daily-watchlist --location us-central1
   ```
   - Ensure `state` is `ENABLED`
   - Check `schedule` and `timeZone` are correct

2. **Check Service Account Permissions**:
   ```bash
   gcloud run services get-iam-policy brooks-briefing-api \
     --region us-central1
   ```
   - Verify service account has `roles/run.invoker`

3. **Check API Service Status**:
   ```bash
   gcloud run services describe brooks-briefing-api --region us-central1
   ```
   - Ensure service is deployed and running

### Authentication Errors

If you see authentication errors:

1. **Verify OIDC Configuration**:
   ```bash
   gcloud scheduler jobs describe brooks-daily-watchlist \
     --location us-central1 \
     --format="yaml(oidcToken)"
   ```

2. **Re-grant Permissions**:
   ```bash
   gcloud run services add-iam-policy-binding brooks-briefing-api \
     --region us-central1 \
     --member="serviceAccount:cloud-scheduler-sa@mikebrooks.iam.gserviceaccount.com" \
     --role="roles/run.invoker"
   ```

### API Errors

Check Cloud Run logs for API errors:

```bash
gcloud logs read \
  --project=mikebrooks \
  --region=us-central1 \
  --service=brooks-briefing-api \
  --limit=100 \
  --filter="severity>=ERROR"
```

### Time Zone Issues

The job uses `America/Los_Angeles` timezone which automatically handles:
- **PST** (Pacific Standard Time): UTC-8
- **PDT** (Pacific Daylight Time): UTC-7

The scheduler automatically adjusts for daylight saving time.

## Monitoring

### View Execution History

```bash
# List recent executions
gcloud scheduler jobs describe brooks-daily-watchlist \
  --location us-central1 \
  --format="yaml(schedule,timeZone,state,lastAttemptTime)"
```

### Set Up Alerts

You can set up Cloud Monitoring alerts for:
- Failed job executions
- API errors during report generation
- Missing reports in Firestore

## Environment Variables

The setup scripts use these environment variables (with defaults):

| Variable | Default | Description |
|----------|---------|-------------|
| `GCP_PROJECT_ID` | `mikebrooks` | GCP project ID |
| `REGION` | `us-central1` | GCP region |
| `API_SERVICE_NAME` | `brooks-briefing-api` | Cloud Run API service name |
| `SCHEDULER_JOB_NAME` | `brooks-daily-watchlist` | Scheduler job name |
| `SERVICE_ACCOUNT_EMAIL` | (auto-created) | Service account email |

## Related Files

- `scripts/setup_scheduler.sh` - Setup script (Bash)
- `scripts/setup_scheduler.ps1` - Setup script (PowerShell)
- `scripts/test_scheduler_job.sh` - Test script (Bash)
- `scripts/test_scheduler_job.ps1` - Test script (PowerShell)
- `scripts/run_daily_watchlist_report.py` - Standalone script (alternative approach)
- `app/main.py` - API endpoint definition

## Alternative: Cloud Run Job

Instead of using Cloud Scheduler + HTTP endpoint, you could also:
1. Deploy `scripts/run_daily_watchlist_report.py` as a Cloud Run Job
2. Schedule the job using Cloud Scheduler

This approach is useful if you want to run the script directly without going through the API.

