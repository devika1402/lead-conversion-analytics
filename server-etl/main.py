# server-etl/main.py
import os
import requests
import psycopg2
import random
from datetime import datetime, timedelta

# Environment
API_URL = os.getenv("API_URL")
conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS")
)
cur = conn.cursor()


def generate_leads():
    today = datetime.now().date()
    three_months_ago = today - timedelta(days=90)
    leads = []

    for i in range(30):
        name = random.choice(['John Doe', 'Jane Smith', 'Alice Johnson'])
        email = f"{name.split()[0].lower()}{i}@example.com"
        phone = f"123-456-78{i:02d}"
        creation_date = three_months_ago + timedelta(days=random.randint(0, 89))
        converted = random.choice([True, False])
        conversion_date = creation_date + timedelta(days=random.randint(1, 10)) if converted else None

        lead = {
            'name': name,
            'email': email,
            'phone': phone,
            'source': random.choice(['Online', 'Referral', 'Social Media']),
            'creation_date': creation_date,
            'status': 'Converted' if converted else 'New',
            'lead_score': random.randint(50, 100),
            'preferred_communication': 'Email',
            'converted_to_member': converted,
            'conversion_date': conversion_date,
            'conversion_channel': random.choice(['Website', 'Referral', 'Social Media']) if converted else None,
            'staff_id': random.randint(1, 3),
            'club_id': random.randint(1, 3)
        }
        leads.append(lead)
    return leads


def upsert_lead(lead):
    cur.execute("""
    INSERT INTO lead (name, email, phone, source, creation_date, status, lead_score,
                      preferred_communication, converted_to_member, conversion_channel,
                      staff_id, club_id)
    VALUES (%(name)s, %(email)s, %(phone)s, %(source)s, %(creation_date)s, %(status)s,
            %(lead_score)s, %(preferred_communication)s, %(converted_to_member)s,
            %(conversion_channel)s, %(staff_id)s, %(club_id)s)
    """, lead)
    conn.commit()

def main():
    leads = generate_leads()
    for lead in leads:
        upsert_lead(lead)
    print(f"Generated and loaded {len(leads)} leads.")

if __name__ == "__main__":
    main()