#!/bin/bash
echo "Deleting old pod..."
kubectl delete pod -l app=onos-ctrl
sleep 5

echo "Waiting for ONOS pod to be ready..."
while true; do
  POD=$(kubectl get pods | grep onos-ctrl | grep Running | awk '{print $1}' | head -n 1)
  if [ ! -z "$POD" ]; then
    READY=$(kubectl get pod $POD -o jsonpath='{.status.containerStatuses[0].ready}')
    if [ "$READY" == "true" ]; then
      echo "ONOS pod $POD is ready."
      break
    fi
  fi
  sleep 5
done

echo "Waiting for ONOS REST API..."
while true; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" -u onos:rocks http://localhost:30181/onos/v1/applications)
  if [ "$STATUS" == "200" ]; then
    echo "REST API is up."
    break
  fi
  sleep 5
done

echo "Activating ODTN service..."
curl -s -u onos:rocks -X POST http://localhost:30181/onos/v1/applications/org.onosproject.odtn-service/active
echo ""

echo "Waiting 30 seconds for ODTN driver bundle to activate..."
sleep 30

echo "Forcing a netcfg update by modifying and restoring the config..."
curl -s -u onos:rocks -X DELETE http://localhost:30181/onos/v1/network/configuration/devices/netconf:10.42.0.1:11001
curl -s -u onos:rocks -X DELETE http://localhost:30181/onos/v1/network/configuration/devices/netconf:10.42.0.1:11002
curl -s -u onos:rocks -X DELETE http://localhost:30181/onos/v1/network/configuration/devices/netconf:10.42.0.1:11003
curl -s -u onos:rocks -X DELETE http://localhost:30181/onos/v1/network/configuration/devices/netconf:10.42.0.1:11004
sleep 2

echo "Pushing Netcfg..."
curl -s -u onos:rocks -X POST -H 'Content-Type: application/json' -d @netcfg-docker.json http://localhost:30181/onos/v1/network/configuration
echo ""

echo "Done."
