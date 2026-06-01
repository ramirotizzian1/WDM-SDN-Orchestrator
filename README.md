# Laboratorio de Comunicaciones Ópticas Virtualizado (SDN + WDM)

Este proyecto es una simulación avanzada de una red óptica desglosada (*Disaggregated Optical Network*) utilizando el modelo ODTN (Open Disaggregated Transport Network), diseñado para demostrar el aprovisionamiento dinámico de *lambdas* basado en la viabilidad de la capa física (QoT) y la orquestación mediante SDN. 

Desarrollado como parte de las prácticas profesionales de Ingeniería de Telecomunicaciones.

## Arquitectura del Sistema

El entorno está distribuido y orquestado mediante microservicios y emulación nativa de hardware:

1. **Orquestación (Kubernetes/K3s y Docker):**
    * **ONOS (SDN Controller):** Actúa como el cerebro de la red. Gestiona la topología lógica y el descubrimiento de dispositivos a través del protocolo NETCONF/YANG.
    * **GNPy (PCE - Path Computation Engine):** Motor de cálculo de la capa física que valida parámetros como la OSNR/GSNR antes de aprovisionar un circuito óptico.

2. **Emulación de Red (Fase 2 - OpenConfig/Cassini):**
    * Se emplean contenedores Docker (`oc-cassini`) que ejecutan el motor **Sysrepo + Netopeer2**.
    * Emulan hardware *Lumentum Whitebox* (EDGECORE Cassini) nativo con modelos YANG estándar del consorcio **OpenConfig**.
    * Interacción 100% estandarizada con ONOS, presentándose como nodos `TERMINAL_DEVICE` WDM con soporte TAPI.

3. **Plano de Control Automatizado (Python Bridge):**
    * Un orquestador inteligente (`bridge_agent.py`) que actúa como "Optical Line System" (OLS).
    * Lee la topología física, consulta la viabilidad de los canales 16-QAM/QPSK a GNPy, e inyecta dinámicamente **FlowRules** (Cross-connects WDM) a los emuladores utilizando la API REST de ONOS.

4. **Dashboard Interactivo (React):**
    * Una interfaz web moderna que dibuja la topología en tiempo real y consume métricas directamente de ONOS y del Python Bridge.
    * Permite **simular cortes de fibra** para desencadenar eventos de restauración automática de enrutamiento (Restoration).

## Evolución del Proyecto

### Fase 1: Mininet-Optical
El laboratorio inició operando con *Mininet-Optical*, emulando ROADMs Lumentum y tramos de fibra G.652. Se logró el enrutamiento exitoso consultando a la API REST de GNPy, orquestando el plano de datos mediante reglas estáticas inyectadas por el `bridge_agent`.

### Fase 2: TAPI, OpenConfig y Carrier-Class
Para elevar el proyecto a estándares Carrier-Class de la industria (SDN comercial):
* Se migró la capa de datos a una red de contenedores Docker individuales con **Netopeer2**, descartando Mininet para evitar colisiones del sistema de host.
* Se resolvió el *Race Condition* de los *Drivers* de ONOS asegurando la sincronización de carga (script `fix_onos2.sh`), logrando utilizar el driver `cassini-openconfig`.
* Los contenedores fueron mapeados exitosamente como dispositivos TAPI en ONOS, exponiendo de manera correcta los puertos Cliente (Add/Drop) y los puertos Ópticos (Line/WDM).
* Aprovisionamiento Estático WDM: El orquestador Python rutea la red interactuando con los puertos `1100X` asignados a cada ROADM contenedorizado, cerrando el ciclo SDN.

## Requisitos de Instalación

- Docker y Docker Compose
- Python 3.10+ (Entorno Virtual)
- Node.js 18+
- Minikube o K3s (Para el clúster de ONOS y GNPy)

## Guía de Uso Rápido

1. **Desplegar Controladores (K3s):**
   ONOS y GNPy deben estar operativos y exponiendo sus puertos correspondientes (`30181` REST, `30101` SSH para ONOS).

2. **Levantar la Red WDM (Fase 2):**
   ```bash
   cd docker-openconfig-emulator
   docker-compose up -d
   ./fix_onos2.sh
   ```

3. **Iniciar el Agente OLS (Puente Python):**
   Este agente escucha en el puerto 5000 y orquesta las rutas WDM.
   ```bash
   source .venv/bin/activate
   sudo python3 bridge_agent.py
   ```

4. **Iniciar el Dashboard Web:**
   ```bash
   cd optical-dashboard
   npm run dev
   ```

5. **Interactuar:**
   Abre el dashboard, visualiza las métricas en vivo de los ROADMs, y haz clic en **"Simular Corte de Fibra"** para ver cómo ONOS y GNPy trabajan en conjunto para restablecer el *Lightpath*.

## Tecnologías Implementadas
* SDN (ONOS, OpenFlow, NETCONF, TAPI)
* Telecomunicaciones Ópticas (WDM, QoT, OSNR, GNPy)
* Modelos de Datos (YANG, OpenConfig)
* Orquestación (Docker, Kubernetes)
* Frontend & Middleware (React, Vite, Flask, NetworkX)

---
*Mantenido por Ramiro Tizzian - Estudiante de Ingeniería en Telecomunicaciones*
