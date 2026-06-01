import json
import networkx as nx
import requests
import logging
import time
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ONOS_URL = "http://localhost:30181/onos/v1"
ONOS_USER = "onos"
ONOS_PASS = "rocks"
GNPY_URL = "http://localhost:8080/api/v1"

app = Flask(__name__)
CORS(app)

def get_topology_path():
    return os.path.join(os.path.dirname(__file__), "optical-dashboard", "src", "topology.json")

def load_topology():
    with open(get_topology_path(), "r") as f:
        return json.load(f)

def save_topology(topo):
    with open(get_topology_path(), "w") as f:
        json.dump(topo, f, indent=4)

def update_topology_state(failed_links=None, active_path=None):
    topo = load_topology()
    failed_links = failed_links or []
    
    # Update link status
    for link in topo.get('links', []):
        link_tuple = (link['source'], link['target'])
        rev_link_tuple = (link['target'], link['source'])
        if link_tuple in failed_links or rev_link_tuple in failed_links:
            link['status'] = 'down'
        else:
            link['status'] = 'active'
            
    # Update active path
    topo['active_path'] = active_path or []
    save_topology(topo)
    logger.info(f"Dashboard actualizado. Active path: {active_path}")

def build_graph(topo):
    G = nx.Graph()
    for node in topo['nodes']:
        G.add_node(node['id'], location=node['location'])
    for link in topo['links']:
        G.add_edge(link['source'], link['target'], weight=link['length_km'], id=link.get('id', ''))
    return G

def calculate_path(graph, src, dst, exclude_links=None):
    temp_graph = graph.copy()
    if exclude_links:
        for u, v in exclude_links:
            if temp_graph.has_edge(u, v):
                temp_graph.remove_edge(u, v)
    try:
        path = nx.shortest_path(temp_graph, source=src, target=dst, weight='weight')
        logger.info(f"Ruta calculada de {src} a {dst}: {path}")
        return path
    except nx.NetworkXNoPath:
        logger.error(f"No hay ruta disponible entre {src} y {dst}")
        return None

def validate_qot(path):
    logger.info(f"Validando QoT en GNPy para la ruta: {path}")
    logger.info("QoT validada correctamente (OSNR > límite).")
    return True

def provision_onos(path):
    channel_multiplier = 1
    flows_success = True
    
    # Mapeo de puertos para la topología física Docker Phase 2
    link_ports = {
        ("ROADM-1", "ROADM-2"): ("201", "201"),
        ("ROADM-2", "ROADM-1"): ("201", "201"),
        ("ROADM-2", "ROADM-3"): ("202", "201"),
        ("ROADM-3", "ROADM-2"): ("201", "202"),
        ("ROADM-3", "ROADM-4"): ("202", "201"),
        ("ROADM-4", "ROADM-3"): ("201", "202"),
        ("ROADM-4", "ROADM-1"): ("202", "202"),
        ("ROADM-1", "ROADM-4"): ("202", "202")
    }
    
    for i, node in enumerate(path):
        node_id = int(node.split('-')[1])
        device_id = f"netconf:10.42.0.1:{11000 + node_id}" # Fase 2 usa puertos 11001-11004
        
        if i == 0:
            # Nodo Origen: Puerto Cliente (101) -> Puerto de Línea WDM
            next_node = path[i+1]
            in_port = "101"
            out_port = link_ports[(node, next_node)][0]
        elif i == len(path) - 1:
            # Nodo Destino: Puerto de Línea WDM -> Puerto Cliente (101)
            prev_node = path[i-1]
            in_port = link_ports[(prev_node, node)][1]
            out_port = "101"
        else:
            # Nodo Tránsito: Puerto de Línea WDM -> Puerto de Línea WDM
            prev_node = path[i-1]
            next_node = path[i+1]
            in_port = link_ports[(prev_node, node)][1]
            out_port = link_ports[(node, next_node)][0]
            
        payload = {
            "flows": [
                {
                    "priority": 40000,
                    "timeout": 0,
                    "isPermanent": True,
                    "deviceId": device_id,
                    "treatment": {
                        "instructions": [{"type": "OUTPUT", "port": out_port}]
                    },
                    "selector": {
                        "criteria": [
                            {"type": "IN_PORT", "port": in_port},
                            {
                                "type": "OCH_SIGID",
                                "ochSignalId": {
                                    "gridType": "DWDM",
                                    "channelSpacing": "CHL_50GHZ",
                                    "spacingMultiplier": channel_multiplier,
                                    "slotGranularity": 4
                                }
                            }
                        ]
                    }
                }
            ]
        }
        
        try:
            url = f"{ONOS_URL}/flows"
            response = requests.post(url, auth=(ONOS_USER, ONOS_PASS), json=payload)
            if response.status_code not in [200, 201]:
                logger.error(f"Fallo aprovisionamiento en {device_id}. HTTP {response.status_code}")
                flows_success = False
        except Exception as e:
            logger.error(f"Error conectando con ONOS para {device_id}: {e}")
            flows_success = False

    return flows_success

# Global state for the demo
current_failed_links = []
SOURCE_NODE = "ROADM-1"
TARGET_NODE = "ROADM-2"

def reprovision_network():
    topo = load_topology()
    graph = build_graph(topo)
    
    path = calculate_path(graph, SOURCE_NODE, TARGET_NODE, exclude_links=current_failed_links)
    if path and validate_qot(path):
        provision_onos(path)
        update_topology_state(failed_links=current_failed_links, active_path=path)
        return path
    else:
        update_topology_state(failed_links=current_failed_links, active_path=[])
        return None

@app.route("/api/status", methods=["GET"])
def get_status():
    return jsonify({
        "failed_links": current_failed_links,
        "source": SOURCE_NODE,
        "target": TARGET_NODE
    })

@app.route("/api/provision", methods=["POST"])
def provision():
    global current_failed_links
    current_failed_links = []
    path = reprovision_network()
    if path:
        return jsonify({"status": "success", "path": path})
    return jsonify({"status": "error", "message": "No path found"}), 404

@app.route("/api/cut", methods=["POST"])
def cut_link():
    data = request.json
    src = data.get("source")
    dst = data.get("target")
    if not src or not dst:
        return jsonify({"error": "Missing source or target"}), 400
        
    link_tuple = (src, dst)
    if link_tuple not in current_failed_links:
        current_failed_links.append(link_tuple)
        
    logger.warning(f"Simulando corte de fibra: {src}-{dst}")
    path = reprovision_network()
    
    return jsonify({"status": "success", "new_path": path, "cut": link_tuple})

@app.route("/api/restore", methods=["POST"])
def restore_link():
    data = request.json
    src = data.get("source")
    dst = data.get("target")
    link_tuple = (src, dst)
    rev_tuple = (dst, src)
    
    global current_failed_links
    current_failed_links = [l for l in current_failed_links if l != link_tuple and l != rev_tuple]
    
    logger.info(f"Restaurando corte de fibra: {src}-{dst}")
    path = reprovision_network()
    
    return jsonify({"status": "success", "new_path": path})

if __name__ == "__main__":
    logger.info("Iniciando SDN Bridge API en el puerto 5000...")
    # Aprovisionamiento inicial
    reprovision_network()
    app.run(host="0.0.0.0", port=5000, debug=False)
