# api-server/app.py
from flask import Flask, jsonify
from datetime import date, timedelta
import random

app = Flask(__name__)


SOURCE_IDS = {'Online': 1, 'Referral': 2, 'Social Media': 3}
COMM_IDS   = {'Email': 1, 'Phone': 2}

def make_lead(external_id):
    # simulate realistic data
    name = random.choice(["John Doe","Jane Smith","Alice Johnson"])
    created = date.today() - timedelta(days=random.randint(0,90))
    converted = random.choice([True, False])
    return {
      "external_id": external_id,
      "name": name,
      "email": f"{name.split()[0].lower()}{external_id}@example.com",
      "phone": f"555-01{external_id:02d}",
      "source":     SOURCE_IDS[random.choice(list(SOURCE_IDS))],
      "creation_date": created.isoformat(),
      "status":     "Converted" if converted else "New",
      "lead_score": random.randint(50,100),
      "preferred_communication": COMM_IDS[random.choice(list(COMM_IDS))],
      "converted_to_member": converted,
      "conversion_date": (created + timedelta(days=random.randint(1,10))).isoformat() if converted else None,
      "conversion_channel": random.choice(list(SOURCE_IDS.keys())) if converted else None,
      "staff_id":   random.randint(1,3),
      "club_id":    random.randint(1,3)
    }

@app.route('/leads', methods=['GET'])
def get_leads():
    # return 10 example leads
    leads = [make_lead(i) for i in range(1,11)]
    return jsonify(leads)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)