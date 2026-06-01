import requests

payload = {
    "flows": [
        {
            "priority": 40000,
            "timeout": 0,
            "isPermanent": True,
            "deviceId": "netconf:10.42.0.1:1831",
            "treatment": {
                "instructions": [{"type": "OUTPUT", "port": "5101"}]
            },
            "selector": {
                "criteria": [
                    {"type": "IN_PORT", "port": "4101"},
                    {
                        "type": "OCH_SIGID",
                        "ochSignalId": {
                            "gridType": "DWDM",
                            "channelSpacing": "CHL_50GHZ",
                            "spacingMultiplier": 1,
                            "slotGranularity": 4
                        }
                    }
                ]
            }
        }
    ]
}

response = requests.post(
    "http://localhost:30181/onos/v1/flows",
    auth=('onos', 'rocks'),
    json=payload
)
print(response.status_code, response.text)
