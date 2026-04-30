# Dryad Zip Uploader

Upload `.zip` files to a Dryad dataset **sequentially (one at a time)** with retries, logging, and safety checks.

---

## 🚀 Features

- Uploads multiple `.zip` files **one-by-one**
- Progress bar for each upload
- Automatic retries on failure
- Skips already uploaded files (local + remote checks)
- Dry-run mode (no uploads, preview only)
- Confirmation prompt before upload
- Logs + CSV report output

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
python scripts/create_dataset_and_upload_zips.py
```

---

## ▶️ Real Upload

Set in `.env`:

```
DRY_RUN=false
```

Then run:

```bash
python scripts/create_dataset_and_upload_zips.py
```

---

## 🔄 How It Works

For each `.zip` file:

1. Validates file
2. Checks if already uploaded
3. Uploads with progress bar
4. Retries if needed
5. Moves to next file

✔️ Files are uploaded **one at a time (not in parallel)**

---

## 📊 Outputs

After running, the script generates:

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

- Skips files already uploaded (local + Dryad)
- Requires confirmation before uploading (optional)
- Dry-run mode prevents accidental uploads
- Retries transient failures automatically
- Does NOT submit dataset for curation

---

## ⚠️ Notes

- Uploads are **not parallel**
- Each file must complete before the next begins
- Large files (10GB+) may take significant time
- Retry logic helps recover from transient API/network issues

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

### Upload failures
- Check logs: `logs/upload.log`
- Retry will happen automatically

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