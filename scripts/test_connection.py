import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from dryad.client import DryadClient


load_dotenv()

client = DryadClient(
    domain=os.environ["DRYAD_DOMAIN"],
    client_id=os.environ["DRYAD_CLIENT_ID"],
    client_secret=os.environ["DRYAD_CLIENT_SECRET"],
)

result = client.test_connection()
print(result)