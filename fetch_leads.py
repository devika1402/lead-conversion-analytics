from __future__ import annotations
import base64, json, os, sys, textwrap
from pathlib import Path

from dotenv import load_dotenv
import os
import requests
import psycopg2
from psycopg2.extras import execute_batch
from cryptography.fernet import Fernet, InvalidToken    

load_dotenv()
# ─────────────────────────────────────────────────────────────────────────────
# 1.  Acquire raw JSON either from API
# ─────────────────────────────────────────────────────────────────────────────
def read_from_file() -> list[dict] | None:
    enc_path = Path(os.getenv("DATA_FILE", "data.enc"))
    if not enc_path.exists():
        return None

    key_b64 = os.getenv("DECRYPT_KEY")
    if not key_b64:
        print("DECRYPT_KEY not set; skipping data.enc", file=sys.stderr)
        return None

    try:
        f = Fernet(key_b64.encode())
        decrypted = f.decrypt(enc_path.read_bytes())
        return json.loads(decrypted)
    except (InvalidToken, ValueError, json.JSONDecodeError) as ex:
        print(f"  Could not decrypt/parse {enc_path.name}: {ex}", file=sys.stderr)
        return None


def read_from_api() -> list[dict]:
    api = os.getenv("API_URL", "http://localhost:8000/leads")
    r = requests.get(api, timeout=10)
    r.raise_for_status()
    return r.json()


def acquire() -> list[dict]:
    data = read_from_file()
    if data is not None:
        print(f" Loaded {len(data)} leads from encrypted file.")
        return data
    print(" Falling back to API…")
    return read_from_api()


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Normalise 
# ─────────────────────────────────────────────────────────────────────────────
SOURCE_MAP = {1: "Online", 2: "Referral", 3: "Social Media"}
COMM_MAP   = {1: "Email",  2: "Phone"}

def norm(rec: dict) -> dict:
    return {
        "name":  rec.get("name"),
        "email": rec.get("email"),
        "phone": rec.get("phone"),
        "source": SOURCE_MAP.get(rec.get("source"), rec.get("source")),
        "created_date": rec.get("created_date") or rec.get("creation_date"),
        "status": rec.get("status"),
        "lead_score": rec.get("lead_score"),
        "preferred_communication":
            COMM_MAP.get(rec.get("preferred_communication"),
                         rec.get("preferred_communication")),
        "conversion_date":     rec.get("conversion_date"),
        "converted_to_member": rec.get("converted_to_member"),
        "conversion_channel":  rec.get("conversion_channel"),
        "staff_id":            rec.get("staff_id"),
        "club_id":             rec.get("club_id"),
    }

# ─────────────────────────────────────────────────────────────────────────────
# 3.  Up-sert into Postgres
# ─────────────────────────────────────────────────────────────────────────────
INSERT = """
INSERT INTO lead
      (name, email, phone, source, created_date, status, lead_score,
       preferred_communication, converted_to_member, conversion_date,
       conversion_channel, staff_id, club_id)
VALUES (%(name)s, %(email)s, %(phone)s, %(source)s, %(created_date)s,
        %(status)s, %(lead_score)s, %(preferred_communication)s,
        %(converted_to_member)s, %(conversion_date)s,
        %(conversion_channel)s, %(staff_id)s, %(club_id)s)
ON CONFLICT (email) DO UPDATE SET
    phone=EXCLUDED.phone, source=EXCLUDED.source,
    created_date=EXCLUDED.created_date, status=EXCLUDED.status,
    lead_score=EXCLUDED.lead_score,
    preferred_communication=EXCLUDED.preferred_communication,
    converted_to_member=EXCLUDED.converted_to_member,
    conversion_date=EXCLUDED.conversion_date,
    conversion_channel=EXCLUDED.conversion_channel,
    staff_id=EXCLUDED.staff_id, club_id=EXCLUDED.club_id;
"""

def load(batch: list[dict]) -> None:
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        dbname=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", os.getenv("USER")),
        password=os.getenv("DB_PASS", "")
    )
    with conn, conn.cursor() as cur:
        ensure_lookups(batch, cur)
        execute_batch(cur, INSERT, batch, page_size=200)
    conn.close()

def drift_report(sample: dict) -> None:
    db_cols = [
        "name","email","phone","source","created_date","status","lead_score",
        "preferred_communication","conversion_date","converted_to_member",
        "conversion_channel","staff_id","club_id"
    ]
    api_cols = list(sample.keys())
    print("\n── Schema drift ───────────────────────────────")
    print("Missing in API :", sorted(set(db_cols) - set(api_cols)))
    print("Extra in API   :", sorted(set(api_cols) - set(db_cols)))
    print("───────────────────────────────────────────────\n")

def ensure_lookups(records: list[dict], cur) -> None:
    # up-sert CLUB
    club_rows = {(r["club_id"], f"Club {r['club_id']}") for r in records if r["club_id"]}
    execute_batch(
        cur,
        "INSERT INTO club (club_id, name) VALUES (%s, %s) "
        "ON CONFLICT (club_id) DO NOTHING;",
        list(club_rows)
    )
    # up-sert STAFF 
    staff_rows = {(r["staff_id"], f"Staff {r['staff_id']}", r["club_id"])
                  for r in records if r["staff_id"]}
    execute_batch(
        cur,
        "INSERT INTO staff (staff_id, name, club_id) VALUES (%s, %s, %s) "
        "ON CONFLICT (staff_id) DO NOTHING;",
        list(staff_rows)
    )

# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    raw = acquire()
    if not raw:
        print("No data. Nothing to do.")
        return
    drift_report(raw[0])
    load([norm(r) for r in raw])
    print(f" Imported / updated {len(raw)} leads.")

if __name__ == "__main__":
    main()


