# AI Context: Dryad Zip Uploader

## Overview

This project is a Python-based tool for uploading `.zip` files to a Dryad dataset via the Dryad API.

It is designed to:
- Upload files **sequentially (one at a time)**
- Handle large files (10GB–25GB+)
- Be safe for non-technical users
- Recover from failures using retries and a manifest

---

## Core Workflow

The upload process follows this exact sequence:

1. Authenticate via OAuth (client credentials)
2. Select or create a dataset
3. For each `.zip` file:
   - Validate file
   - Check if already uploaded
   - Upload file
   - Retry on failure
4. Write logs and reports

---

## Key Constraints

- Uploads must use the **Dryad dataset identifier**, not the numeric ID
- Example identifier:
  ```
  doi:10.5061/dryad.xxxxx
  ```
- Must be URL-encoded for API calls:
  ```
  doi%3A10.5061%2Fdryad.xxxxx
  ```

- Upload endpoint:
  ```
  PUT /api/v2/datasets/<encoded-identifier>/files/<filename>
  ```

- Files are uploaded as raw binary (not chunked)

---

## Project Structure

```
project-root/
├── src/dryad/
│   └── client.py                # API client (auth, upload, list files)
│
├── scripts/
│   └── create_dataset_and_upload_zips.py   # Main script
│
├── data/                        # Input zip files
├── logs/                        # Runtime logs
├── reports/                     # CSV reports
├── upload_manifest.json         # Upload state tracking
│
├── .env                         # Configuration
├── .env.example                 # Template config
├── README.md                    # Human instructions
├── AI_CONTEXT.md                # This file
```

---

## Configuration (via `.env`)

Key variables:

```
DRYAD_DOMAIN=datadryad.org
DRYAD_CLIENT_ID=...
DRYAD_CLIENT_SECRET=...

USE_EXISTING_DATASET=true
EXISTING_DATASET_IDENTIFIER=doi%3A10.5061%2Fdryad.xxxxx

MAX_RETRIES=5
RETRY_DELAY_SECONDS=15

DRY_RUN=true
REQUIRE_CONFIRMATION=true
ALLOW_EXISTING_REMOTE_FILES=false
```

---

## Important Behaviors

### Sequential Execution
Files are processed in a simple loop:

```
for file in files:
    upload(file)
```

There is **no parallelism**.

---

### Retry Logic
- Retries each file up to `MAX_RETRIES`
- Waits `RETRY_DELAY_SECONDS` between attempts
- Retries are used for:
  - transient API errors
  - network issues
  - Dryad inconsistencies

---

### Manifest Tracking

`upload_manifest.json` tracks:

```
uploaded_files
failed_files
```

Used to:
- prevent re-uploading completed files
- resume interrupted runs

---

### Remote File Detection

The script calls:

```
GET /api/v2/datasets/<identifier>/files
```

Then skips files already present in Dryad.

---

### Dry Run Mode

When:

```
DRY_RUN=true
```

The script:
- lists files
- prints plan
- does NOT upload anything

---

## Logging & Outputs

### Logs
```
logs/upload.log
```

### CSV Report
```
reports/upload_report_<timestamp>.csv
```

Columns:
```
filename,status,size_bytes,size_gb,uploaded_at,error
```

---

## Upload Mechanics

Uploads use:

```
requests.put(...)
```

With:
- `Content-Length` set
- binary file stream
- progress tracked via wrapper (not generator)

Important:
- DO NOT use chunked encoding
- DO NOT stream via generator (breaks Dryad)

---

## Known Edge Cases

1. **Intermittent 401 on auth**
   - Fixed via retry logic in `authenticate()`

2. **404 after upload completes**
   - Dryad may not immediately register file
   - Retry resolves this

3. **Duplicate filenames**
   - Skipped unless `ALLOW_EXISTING_REMOTE_FILES=true`

4. **Sparse test files**
   - `fallocate` creates compressible data
   - use `/dev/urandom` for realistic testing

---

## Extending the Project

### Safe Enhancements

- Add throughput/ETA metrics
- Add parallel uploads (careful: Dryad limits unknown)
- Add dataset submission step
- Add CLI interface (argparse)
- Package as installable tool

---

### Risky Changes (avoid unless careful)

- Switching to chunked uploads
- Removing Content-Length
- Parallel uploads without rate limiting
- Modifying identifier encoding

---

## How to Use AI with This Project

An AI should:

- Treat `client.py` as the API abstraction layer
- Treat `create_dataset_and_upload_zips.py` as orchestration
- Never modify upload logic without preserving:
  - Content-Length
  - raw binary upload
  - identifier encoding

If debugging:
1. Check logs
2. Check manifest
3. Check Dryad response body
4. Verify identifier encoding

---

## Summary

This project is a **resilient, sequential uploader** for large datasets to Dryad, designed for:

- safety
- recoverability
- ease of use

It prioritizes correctness over speed and is suitable for very large uploads (100GB+).