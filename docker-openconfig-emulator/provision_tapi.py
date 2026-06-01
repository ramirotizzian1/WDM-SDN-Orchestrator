import requests
import json

ONOS_URL = "http://localhost:30181/onos/restconf/data/tapi-common:context"
AUTH = ("onos", "rocks")
HEADERS = {"Content-Type": "application/json"}

# 1. Fetch SIPs
print("Fetching TAPI SIPs...")
resp = requests.get(ONOS_URL, auth=AUTH)
context = resp.json().get("tapi-common:context", {})
sips = context.get("service-interface-point", [])

uuid_src = None
uuid_dst = None

for sip in sips:
    names = sip.get("name", [])
    for n in names:
        val = n.get("value", "")
        if "11001/101" in val:
            uuid_src = sip.get("uuid")
        if "11003/101" in val:
            uuid_dst = sip.get("uuid")

if not uuid_src or not uuid_dst:
    print(f"Could not find SIPs! Src: {uuid_src}, Dst: {uuid_dst}")
    exit(1)

print(f"Found Src SIP: {uuid_src}")
print(f"Found Dst SIP: {uuid_dst}")

# 2. Create Connectivity Service Payload
service_uuid = "service-tapi-100G-1"

payload = {
    "tapi-connectivity:connectivity-service": [
        {
            "uuid": service_uuid,
            "service-layer": "DSR",
            "service-type": "POINT_TO_POINT_CONNECTIVITY",
            "end-point": [
                {
                    "local-id": "ep1",
                    "layer-protocol-name": "DSR",
                    "service-interface-point": {
                        "service-interface-point-uuid": uuid_src
                    }
                },
                {
                    "local-id": "ep2",
                    "layer-protocol-name": "DSR",
                    "service-interface-point": {
                        "service-interface-point-uuid": uuid_dst
                    }
                }
            ]
        }
    ]
}

print(f"\nProvisioning Connectivity Service {service_uuid}...")
create_url = "http://localhost:30181/onos/restconf/data/tapi-common:context/tapi-connectivity:connectivity-context/"
resp = requests.post(create_url, auth=AUTH, headers=HEADERS, json=payload)
print(f"Response Status: {resp.status_code}")
print(f"Response Text: {resp.text}")

