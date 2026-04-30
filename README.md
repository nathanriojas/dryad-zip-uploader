# Dryad Zip Uploader

Robust Dryad uploader for large ZIP files with sequential uploads, retry logic, and resumable execution.

---

## ⚡ Quick Start

```bash
cp .env.example .env
# edit .env with your credentials and dataset identifier

python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

python scripts/upload_zips.py
```

---

## 🚀 Features

- Uploads multiple `.zip` files **sequentially (one at a time)**
- Progress bar for each upload
- Automatic retries for transient failures
- Skips already uploaded files (local + remote checks)
- Dry-run mode for safe preview
- Confirmation prompt before upload
- Logging + CSV reporting
- Resumable via manifest tracking

---

## 📦 Setup

### 1. Clone repo

```bash
git clone <your-repo-url>
cd <repo-name>
```

### 2. Create virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration

### 1. Create environment file

```bash
cp .env.example .env
```

### 2. Edit `.env`

```env
DRYAD_DOMAIN=datadryad.org
DRYAD_CLIENT_ID=your_client_id
DRYAD_CLIENT_SECRET=your_client_secret

USE_EXISTING_DATASET=true
EXISTING_DATASET_IDENTIFIER=doi%3A10.5061%2Fdryad.your_dataset

MAX_RETRIES=5
RETRY_DELAY_SECONDS=15

DRY_RUN=true
REQUIRE_CONFIRMATION=true
ALLOW_EXISTING_REMOTE_FILES=false
```

---

## 📁 Add Files

Place all `.zip` files in:

```
data/
```

Example:

```
data/
  file1.zip
  file2.zip
  file3.zip
```

---

## 🧪 Dry Run (Recommended First)

Preview what will happen without uploading anything.

Set in `.env`:

```
DRY_RUN=true
```

Run:

```bash
python scripts/upload_zips.py
```

---

## ▶️ Real Upload

Set in `.env`:

```
DRY_RUN=false
```

Then run:

```bash
python scripts/upload_zips.py
```

---

## 🔄 How It Works

For each `.zip` file:

1. Validates file
2. Checks if already uploaded (local + Dryad)
3. Uploads file with progress tracking
4. Retries if needed
5. Moves to next file

✔️ Files are uploaded **one at a time (not in parallel)**

---

## 📊 Outputs

### Logs
```
logs/upload.log
```

### Upload manifest (state tracking)
```
upload_manifest.json
```

### CSV report
```
reports/upload_report_<timestamp>.csv
```

Example CSV:

```
filename,status,size_bytes,size_gb,uploaded_at,error
file1.zip,uploaded,123456,0.12,2026-04-30T..., 
file2.zip,skipped,98765,0.09,,Already exists
file3.zip,failed,54321,0.05,,Error message
```

---

## 🛡️ Safety Features

- Skips files already uploaded (local + remote)
- Requires confirmation before uploading
- Dry-run mode prevents accidental uploads
- Retries transient API/network failures
- Tracks state via manifest for resumability
- Does NOT submit dataset for curation

---

## ⚠️ Notes

- Uploads are **not parallel**
- Each file must complete before the next begins
- Large files (10GB+) may take significant time
- Retry logic handles transient Dryad/API inconsistencies
- Dataset identifier must be URL-encoded (handled via `.env`)

---

## 🧹 Cleanup

To reset local state:

```bash
rm upload_manifest.json
rm -rf logs reports
```

---

## ❓ Troubleshooting

### Authentication errors
- Verify `.env` values
- Ensure no extra spaces or quotes
- Retry (transient failures are possible)

### Upload failures
- Check logs: `logs/upload.log`
- Retry logic will handle most cases automatically

### Files skipped unexpectedly
- Check `upload_manifest.json`
- Check Dryad dataset for existing files

---

## 👤 Intended Usage

This tool is designed so a user can:

1. Drop `.zip` files into `data/`
2. Run one command
3. Upload safely without needing to understand the API

---

## ✅ Summary

```
1. Configure .env
2. Add zip files to data/
3. Run script
4. Done
```