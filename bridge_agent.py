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

SPECTRUM_DB_PATH = os.path.join(os.path.dirname(__file__), "spectrum_db.json")
TOTAL_CHANNELS = 96

def init_spectrum_db():
    topo = load_topology()
    db = {}
    for link in topo.get('links', []):
        link_id = f"{link['source']}-{link['target']}"
        db[link_id] = [0] * TOTAL_CHANNELS
        rev_link_id = f"{link['target']}-{link['source']}"
        db[rev_link_id] = [0] * TOTAL_CHANNELS
    with open(SPECTRUM_DB_PATH, "w") as f:
        json.dump(db, f, indent=4)

def load_spectrum_db():
    if not os.path.exists(SPECTRUM_DB_PATH):
        init_spectrum_db()
    with open(SPECTRUM_DB_PATH, "r") as f:
        return json.load(f)

def save_spectrum_db(db):
    with open(SPECTRUM_DB_PATH, "w") as f:
        json.dump(db, f, indent=4)

def find_available_lambda(path):
    db = load_spectrum_db()
    available_channels = set(range(TOTAL_CHANNELS))
    for i in range(len(path) - 1):
        link_id = f"{path[i]}-{path[i+1]}"
        if link_id in db:
            link_status = db[link_id]
            free_in_link = {ch for ch in available_channels if link_status[ch] == 0}
            available_channels = available_channels.intersection(free_in_link)
    if available_channels:
        return min(available_channels) + 1
    return None

def allocate_lambda(path, lambda_idx):
    db = load_spectrum_db()
    ch_index = lambda_idx - 1
    for i in range(len(path) - 1):
        link_id = f"{path[i]}-{path[i+1]}"
        rev_link_id = f"{path[i+1]}-{path[i]}"
        if link_id in db:
            db[link_id][ch_index] = 1
        if rev_link_id in db:
            db[rev_link_id][ch_index] = 1
    save_spectrum_db(db)
    logger.info(f"Espectro asignado: Lambda {lambda_idx} en {path}")

def free_lambda(path, lambda_idx):
    db = load_spectrum_db()
    ch_index = lambda_idx - 1
    for i in range(len(path) - 1):
        link_id = f"{path[i]}-{path[i+1]}"
        rev_link_id = f"{path[i+1]}-{path[i]}"
        if link_id in db:
            db[link_id][ch_index] = 0
        if rev_link_id in db:
            db[rev_link_id][ch_index] = 0
    save_spectrum_db(db)
    logger.info(f"Espectro liberado: Lambda {lambda_idx} en {path}")

def update_topology_state(failed_links=None, active_path=None, active_lambda=None):
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
    topo['active_lambda'] = active_lambda
    save_topology(topo)
    logger.info(f"Dashboard actualizado. Active path: {active_path} (Lambda: {active_lambda})")

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

def validate_qot(path, topo, modulation="QPSK"):
    logger.info(f"Validando QoT en GNPy para la ruta: {path} con modulación {modulation}")
    
    total_km = 0
    links = topo.get('links', [])
    for i in range(len(path) - 1):
        u, v = path[i], path[i+1]
        for link in links:
            if (link['source'] == u and link['target'] == v) or (link['source'] == v and link['target'] == u):
                total_km += link['length_km']
                break
                
    logger.info(f"Distancia total física: {total_km} km")
    
    thresholds = {"64-QAM": 200, "16-QAM": 400, "QPSK": 2000}
    max_reach = thresholds.get(modulation, 2000)
    
    if total_km > max_reach:
        msg = f"GNPy Rechazó el circuito: OSNR inaceptable para {modulation} a {total_km}km. Límite físico: {max_reach}km."
        logger.error(msg)
        return False, msg
        
    logger.info("QoT validada correctamente (OSNR dentro de márgenes físicos).")
    return True, "OK"

def provision_onos(path, lambda_idx):
    channel_multiplier = lambda_idx
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

def unprovision_onos(path, lambda_idx):
    channel_multiplier = lambda_idx
    flows_success = True
    
    for i, node in enumerate(path):
        node_id = int(node.split('-')[1])
        device_id = f"netconf:10.42.0.1:{11000 + node_id}"
        
        try:
            url = f"{ONOS_URL}/flows/{device_id}"
            response = requests.get(url, auth=(ONOS_USER, ONOS_PASS))
            if response.status_code == 200:
                data = response.json()
                for flow in data.get('flows', []):
                    # Verificar si es nuestro flujo y tiene la lambda exacta
                    is_our_lambda = False
                    for criteria in flow.get('selector', {}).get('criteria', []):
                        if criteria.get('type') == 'OCH_SIGID':
                            if criteria.get('ochSignalId', {}).get('spacingMultiplier') == channel_multiplier:
                                is_our_lambda = True
                                break
                    
                    if is_our_lambda:
                        flow_id = flow.get('id')
                        delete_url = f"{ONOS_URL}/flows/{device_id}/{flow_id}"
                        del_response = requests.delete(delete_url, auth=(ONOS_USER, ONOS_PASS))
                        if del_response.status_code not in [200, 204]:
                            logger.error(f"Error borrando flujo {flow_id} en {device_id}")
                            flows_success = False
                        else:
                            logger.info(f"Flujo {flow_id} borrado de {device_id} (Lambda {lambda_idx})")
            else:
                logger.error(f"Fallo al obtener flujos en {device_id}. HTTP {response.status_code}")
                flows_success = False
        except Exception as e:
            logger.error(f"Error conectando con ONOS para borrar en {device_id}: {e}")
            flows_success = False

    return flows_success

# Global state for the demo
current_failed_links = []
SOURCE_NODE = "ROADM-1"
TARGET_NODE = "ROADM-2"

active_circuits = []
circuit_counter = 0

def provision_circuit(src, dst, force_lambda=None, modulation="QPSK"):
    global circuit_counter
    topo = load_topology()
    graph = build_graph(topo)
    
    path = calculate_path(graph, src, dst, exclude_links=current_failed_links)
    if not path:
        update_topology_state(failed_links=current_failed_links, active_path=[], active_lambda=None)
        return None, "No hay ruta física disponible."
        
    qot_ok, msg = validate_qot(path, topo, modulation)
    if qot_ok:
        if force_lambda is not None:
            new_lambda = int(force_lambda)
            logger.info(f"El usuario forzó la selección de la Lambda: {new_lambda}")
        else:
            new_lambda = find_available_lambda(path)
            
        if new_lambda is None:
            logger.error("Bloqueo RWA: No hay lambdas libres continuas en la ruta.")
            update_topology_state(failed_links=current_failed_links, active_path=[], active_lambda=None)
            return None, "Bloqueo de espectro (sin lambdas disponibles)"
            
        allocate_lambda(path, new_lambda)
        provision_onos(path, new_lambda)
        
        # Guardar en base de datos en memoria
        circuit_counter += 1
        circuit_id = f"CIR-{circuit_counter}"
        circuit_data = {
            "id": circuit_id,
            "src": src,
            "dst": dst,
            "lambda": new_lambda,
            "modulation": modulation,
            "path": path
        }
        active_circuits.append(circuit_data)
        
        update_topology_state(failed_links=current_failed_links, active_path=path, active_lambda=new_lambda)
        return path, new_lambda
    else:
        update_topology_state(failed_links=current_failed_links, active_path=[], active_lambda=None)
        return None, msg

@app.route("/api/status", methods=["GET"])
def get_status():
    return jsonify({
        "failed_links": current_failed_links,
        "source": SOURCE_NODE,
        "target": TARGET_NODE
    })

@app.route("/api/spectrum", methods=["GET"])
def get_spectrum():
    db = load_spectrum_db()
    return jsonify(db)

@app.route("/api/provision", methods=["POST"])
def provision():
    global current_failed_links, SOURCE_NODE, TARGET_NODE
    
    data = request.json or {}
    force_lambda = data.get("force_lambda")
    modulation = data.get("modulation", "QPSK")
    
    if "source" in data and data["source"]:
        SOURCE_NODE = data["source"]
    if "target" in data and data["target"]:
        TARGET_NODE = data["target"]
        
    logger.info(f"Petición de circuito: {SOURCE_NODE} -> {TARGET_NODE} | Modulación: {modulation}")
    
    path, response_data = provision_circuit(SOURCE_NODE, TARGET_NODE, force_lambda=force_lambda, modulation=modulation)
    if path:
        return jsonify({"status": "success", "path": path, "lambda": response_data})
    return jsonify({"status": "error", "message": response_data}), 400

@app.route("/api/free", methods=["POST"])
def free_endpoint():
    data = request.json or {}
    src = data.get("source")
    dst = data.get("target")
    lambda_idx = data.get("force_lambda")
    
    if not src or not dst or not lambda_idx:
        return jsonify({"status": "error", "message": "Debe especificar Origen, Destino y una Lambda"}), 400
        
    topo = load_topology()
    graph = build_graph(topo)
    path = calculate_path(graph, src, dst, exclude_links=current_failed_links)
    
    if path:
        free_lambda(path, int(lambda_idx))
        unprovision_onos(path, int(lambda_idx))
        
        # Eliminar de active_circuits si existe
        global active_circuits
        active_circuits = [c for c in active_circuits if not (c["src"] == src and c["dst"] == dst and c["lambda"] == int(lambda_idx))]
        
        return jsonify({"status": "success", "message": f"Lambda {lambda_idx} liberada exitosamente en ONOS"})
        
    return jsonify({"status": "error", "message": "No se pudo calcular la ruta para liberar"}), 404

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
    
    # Identificar y rerutear todos los circuitos afectados
    global active_circuits
    affected_circuits = []
    
    for c in active_circuits:
        path = c["path"]
        broken = False
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            if (u == src and v == dst) or (u == dst and v == src):
                broken = True
                break
        if broken:
            affected_circuits.append(c)
            
    last_path = None
    for c in affected_circuits:
        logger.info(f"Restauración Masiva: Reruteando circuito {c['id']} ({c['src']}->{c['dst']})")
        # 1. Liberar configuración vieja
        free_lambda(c["path"], c["lambda"])
        unprovision_onos(c["path"], c["lambda"])
        active_circuits.remove(c)
        
        # 2. Aprovisionar nuevo circuito (intentando mantener la misma lambda original)
        new_path, response_data = provision_circuit(c["src"], c["dst"], force_lambda=c["lambda"], modulation=c["modulation"])
        if new_path:
            logger.info(f"Circuito {c['id']} salvado. Nueva ruta: {new_path} con Lambda {c['lambda']}")
            last_path = new_path
        else:
            logger.error(f"Circuito {c['id']} perdido. Causa: {response_data}")
    
    return jsonify({"status": "success", "new_path": last_path, "cut": link_tuple})

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
    
    # Para el demo, al restaurar el cable simplemente limpiamos la UI. 
    # Los circuitos permanecen en sus rutas de backup actuales.
    update_topology_state(failed_links=current_failed_links, active_path=[], active_lambda=None)
    
    return jsonify({"status": "success", "new_path": None})

if __name__ == "__main__":
    logger.info("Iniciando SDN Bridge API en el puerto 5000...")
    app.run(host="0.0.0.0", port=5000, debug=False)
