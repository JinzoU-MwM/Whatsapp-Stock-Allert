import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

URL = "http://localhost:3000/send"
PHONE = os.getenv("TARGET_PHONE")

if not PHONE:
    print("[ERROR] TARGET_PHONE is missing in .env")
    exit(1)

print(f"Sending test message to {PHONE}...")

payload = {
    "number": PHONE,
    "message": "🤖 *StockSignal Bot Connection Test*\n\nIf you see this, the notification system is working! ✅"
}

try:
    response = requests.post(URL, json=payload, timeout=10)
    if response.status_code == 200:
        print("[SUCCESS] Server responded:", response.json())
    else:
        print(f"[FAIL] Status: {response.status_code}")
        print("Response:", response.text)
except Exception as e:
    print(f"[ERROR] Connection Error: {e}")
    print("Make sure 'npm start' is running in whatsapp-service folder!")
