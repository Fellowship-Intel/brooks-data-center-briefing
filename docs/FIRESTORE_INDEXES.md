# Firestore Composite Indexes

This document describes the required Firestore composite indexes for optimal query performance.

## Required Indexes

### 1. daily_reports - client_id + trading_date

**Collection:** `daily_reports`  
**Fields:**
- `client_id` (Ascending)
- `trading_date` (Descending)

**Used by:**
- `list_daily_reports()` when filtering by `client_id` and ordering by `trading_date`

**Create via CLI:**
```bash
gcloud firestore indexes create \
  --collection-group=daily_reports \
  --query-scope=COLLECTION \
  --field-config field-path=client_id,order=ASCENDING \
  --field-config field-path=trading_date,order=DESCENDING \
  --project=YOUR_PROJECT_ID
```

**Or deploy via firestore.indexes.json:**
```bash
gcloud firestore indexes deploy firestore.indexes.json --project=YOUR_PROJECT_ID
```

### 2. daily_reports - client_id + created_at

**Collection:** `daily_reports`  
**Fields:**
- `client_id` (Ascending)
- `created_at` (Descending)

**Used by:**
- `list_daily_reports()` when filtering by `client_id` and ordering by `created_at`

## Automatic Index Creation

Firestore will automatically prompt you to create indexes when you run queries that require them. The error message will include a direct link to create the index in the Firebase Console.

## Performance Notes

- Single-field queries (no filters) don't require composite indexes
- Queries filtering by `client_id` and ordering require composite indexes
- Document ID queries (`get_daily_report()`) don't require indexes (most efficient)
- All queries are cached in memory for 3-5 minutes to reduce Firestore reads

