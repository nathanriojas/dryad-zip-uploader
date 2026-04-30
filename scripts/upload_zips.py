import csv
import json
import logging
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from dryad.client import DryadClient


load_dotenv()

root = Path(__file__).resolve().parents[1]
metadata_path = root / "examples" / "metadata.json"
data_dir = root / "data"
logs_dir = root / "logs"
reports_dir = root / "reports"
manifest_path = root / "upload_manifest.json"

logs_dir.mkdir(exist_ok=True)
reports_dir.mkdir(exist_ok=True)

USE_EXISTING_DATASET = os.getenv("USE_EXISTING_DATASET", "true").lower() == "true"
EXISTING_DATASET_IDENTIFIER = os.getenv("EXISTING_DATASET_IDENTIFIER")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "5"))
RETRY_DELAY_SECONDS = int(os.getenv("RETRY_DELAY_SECONDS", "15"))
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
REQUIRE_CONFIRMATION = os.getenv("REQUIRE_CONFIRMATION", "true").lower() == "true"
ALLOW_EXISTING_REMOTE_FILES = os.getenv("ALLOW_EXISTING_REMOTE_FILES", "false").lower() == "true"

logging.basicConfig(
    filename=logs_dir / "upload.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter("%(message)s"))
logging.getLogger().addHandler(console)


def load_manifest() -> dict:
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    return {"uploaded_files": {}, "failed_files": {}}


def save_manifest(manifest: dict) -> None:
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def file_signature(path: Path) -> dict:
    return {
        "name": path.name,
        "size": path.stat().st_size,
        "last_modified": path.stat().st_mtime,
    }


def validate_zip_files(zip_files: list[Path]) -> None:
    if not zip_files:
        raise FileNotFoundError(f"No .zip files found in {data_dir}")

    seen = set()

    for path in zip_files:
        if path.name in seen:
            raise ValueError(f"Duplicate filename found: {path.name}")

        seen.add(path.name)

        if path.suffix.lower() != ".zip":
            raise ValueError(f"Not a zip file: {path}")

        if path.stat().st_size <= 0:
            raise ValueError(f"Empty zip file found: {path}")


def write_csv_report(rows: list[dict]) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    report_path = reports_dir / f"upload_report_{timestamp}.csv"

    fieldnames = [
        "filename",
        "status",
        "size_bytes",
        "size_gb",
        "uploaded_at",
        "error",
    ]

    with open(report_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return report_path


def should_skip_file(path: Path, manifest: dict, remote_file_names: set[str]) -> bool:
    sig = file_signature(path)

    if path.name in remote_file_names:
        if ALLOW_EXISTING_REMOTE_FILES:
            logging.info(f"Remote file exists but ALLOW_EXISTING_REMOTE_FILES=true; attempting upload: {path.name}")
            return False

        logging.info(f"Skipping {path.name}; already exists remotely.")
        return True

    uploaded = manifest["uploaded_files"].get(path.name)

    if uploaded and uploaded.get("size") == sig["size"]:
        logging.info(f"Skipping {path.name}; already marked uploaded in manifest.")
        return True

    return False


def upload_with_retries(client: DryadClient, dataset_identifier: str, zip_file: Path) -> dict:
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logging.info(f"Upload attempt {attempt}/{MAX_RETRIES}: {zip_file.name}")

            return client.upload_file(
                dataset_identifier=dataset_identifier,
                file_path=str(zip_file),
                description=f"Uploaded file: {zip_file.name}",
            )

        except Exception as e:
            last_error = e
            logging.exception(f"Upload failed on attempt {attempt}: {zip_file.name}")

            if attempt < MAX_RETRIES:
                logging.info(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
                time.sleep(RETRY_DELAY_SECONDS)

    raise last_error


with open(metadata_path, "r", encoding="utf-8") as f:
    metadata = json.load(f)

zip_files = sorted(data_dir.glob("*.zip"))
validate_zip_files(zip_files)

total_size_bytes = sum(path.stat().st_size for path in zip_files)
total_size_gb = total_size_bytes / (1024 ** 3)

logging.info("")
logging.info("====================================")
logging.info("Upload plan")
logging.info("====================================")
logging.info(f"Zip files found: {len(zip_files)}")
logging.info(f"Total size: {total_size_gb:.4f} GB")
logging.info(f"Dry run: {DRY_RUN}")
logging.info(f"Use existing dataset: {USE_EXISTING_DATASET}")

for path in zip_files:
    logging.info(f" - {path.name} ({path.stat().st_size / (1024 ** 3):.4f} GB)")

if DRY_RUN:
    logging.info("")
    logging.info("Dry run complete. No files uploaded.")
    raise SystemExit(0)

if REQUIRE_CONFIRMATION:
    answer = input("\nProceed with upload? Type 'yes' to continue: ").strip().lower()
    if answer != "yes":
        logging.info("Upload cancelled.")
        raise SystemExit(0)

manifest = load_manifest()

client = DryadClient(
    domain=os.environ["DRYAD_DOMAIN"],
    client_id=os.environ["DRYAD_CLIENT_ID"],
    client_secret=os.environ["DRYAD_CLIENT_SECRET"],
)

client.authenticate()
logging.info("Authenticated successfully")

if USE_EXISTING_DATASET:
    if not EXISTING_DATASET_IDENTIFIER:
        raise ValueError("EXISTING_DATASET_IDENTIFIER is required when USE_EXISTING_DATASET=true")

    dataset_identifier = EXISTING_DATASET_IDENTIFIER

    logging.info("")
    logging.info("==============================")
    logging.info("Using existing dataset")
    logging.info("==============================")
    logging.info(f"Dataset identifier: {dataset_identifier}")

else:
    dataset = client.create_dataset(metadata)
    dataset_identifier = dataset["identifier"]

    logging.info("")
    logging.info("==============================")
    logging.info("Created dataset")
    logging.info("==============================")
    logging.info(f"ID: {dataset.get('id')}")
    logging.info(f"Identifier: {dataset_identifier}")
    logging.info(f"Status: {dataset.get('versionStatus')}")

remote_files = client.list_files(dataset_identifier)
remote_file_names = {
    f.get("path") or f.get("filename") or f.get("name")
    for f in remote_files
    if isinstance(f, dict)
}
remote_file_names.discard(None)

uploaded_files = []
skipped_files = []
failed_files = []
report_rows = []

for zip_file in zip_files:
    sig = file_signature(zip_file)
    size_gb = sig["size"] / (1024 ** 3)

    logging.info("")
    logging.info("------------------------------")
    logging.info(f"File: {zip_file.name}")
    logging.info(f"Size: {size_gb:.4f} GB")
    logging.info("------------------------------")

    if should_skip_file(zip_file, manifest, remote_file_names):
        skipped_files.append(zip_file.name)
        report_rows.append({
            "filename": zip_file.name,
            "status": "skipped",
            "size_bytes": sig["size"],
            "size_gb": f"{size_gb:.4f}",
            "uploaded_at": "",
            "error": "Already uploaded or exists remotely",
        })
        continue

    try:
        result = upload_with_retries(client, dataset_identifier, zip_file)

        uploaded_at = datetime.now(UTC).isoformat()
        uploaded_files.append(zip_file.name)

        manifest["uploaded_files"][zip_file.name] = {
            **sig,
            "uploaded_at": uploaded_at,
            "dryad_response": result,
        }

        manifest["failed_files"].pop(zip_file.name, None)
        save_manifest(manifest)

        logging.info("Upload complete")
        logging.info(f"Dryad file status: {result.get('status')}")
        logging.info(f"Dryad file path: {result.get('path')}")
        logging.info(f"Dryad file size: {result.get('size')} bytes")

        report_rows.append({
            "filename": zip_file.name,
            "status": "uploaded",
            "size_bytes": sig["size"],
            "size_gb": f"{size_gb:.4f}",
            "uploaded_at": uploaded_at,
            "error": "",
        })

    except Exception as e:
        failed_files.append(zip_file.name)
        failed_at = datetime.now(UTC).isoformat()

        manifest["failed_files"][zip_file.name] = {
            **sig,
            "failed_at": failed_at,
            "error": str(e),
        }

        save_manifest(manifest)

        logging.error("Upload failed permanently")
        logging.error(f"File: {zip_file.name}")
        logging.error(f"Error: {e}")

        report_rows.append({
            "filename": zip_file.name,
            "status": "failed",
            "size_bytes": sig["size"],
            "size_gb": f"{size_gb:.4f}",
            "uploaded_at": "",
            "error": str(e),
        })

report_path = write_csv_report(report_rows)

logging.info("")
logging.info("====================================")
logging.info("Final summary")
logging.info("====================================")
logging.info(f"Dataset identifier: {dataset_identifier}")
logging.info(f"Total files found: {len(zip_files)}")
logging.info(f"Uploaded this run: {len(uploaded_files)}")
logging.info(f"Skipped: {len(skipped_files)}")
logging.info(f"Failed: {len(failed_files)}")
logging.info(f"CSV report: {report_path}")
logging.info("")
logging.info("Dataset NOT submitted for curation yet.")
logging.info("====================================")