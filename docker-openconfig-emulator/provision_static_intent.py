import requests
import json
import time

ONOS_URL = "http://localhost:30181/onos/v1/intents"
AUTH = ("onos", "rocks")
HEADERS = {"Content-Type": "application/json"}

intent_payload = {
    "type": "OpticalConnectivityIntent",
    "appId": "org.onosproject.cli",
    "priority": 100,
    "src": {
        "device": "netconf:10.42.0.1:11001",
        "port": "201"
    },
    "dst": {
        "device": "netconf:10.42.0.1:11003",
        "port": "201"
    },
    "signalType": "ODU4",
    "isBidirectional": True
}

print("POSTing OpticalConnectivityIntent...")
resp = requests.post(ONOS_URL, auth=AUTH, headers=HEADERS, json=intent_payload)

print(f"Status Code: {resp.status_code}")
if resp.status_code != 201:
    print(f"Response: {resp.text}")
    exit(1)

# Get the location header to find the intent key
location = resp.headers.get("Location")
print(f"Intent created successfully. Location: {location}")

# Check the status of the intent
time.sleep(2)
print("Checking intent status...")
status_resp = requests.get(ONOS_URL, auth=AUTH)
intents = status_resp.json().get("intents", [])

for intent in intents:
    if intent.get("type") == "OpticalConnectivityIntent":
        state = intent.get("state")
        print(f"Intent State: {state}")
