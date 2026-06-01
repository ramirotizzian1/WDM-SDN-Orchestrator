# Proyecto: Laboratorio de Comunicaciones Ópticas Virtualizado (SDN + WDM)

## Contexto del Proyecto

Este laboratorio forma parte de las prácticas profesionales de Ingeniería de Telecomunicaciones. El objetivo es simular una red óptica desglosada (Disaggregated Optical Network) utilizando el modelo ODTN, permitiendo el aprovisionamiento dinámico de lambdas basado en la viabilidad de la capa física (QoT).

## Arquitectura del Sistema

El entorno está distribuido entre un clúster de microservicios y una emulación de host:

1. **Orquestación (Kubernetes/K3s):**
    * **ONOS (SDN Controller):** Gestiona la topología lógica y el descubrimiento de ROADMs. Apps activas: `optical-model`, `odtn-service`, `drivers.lumentum`.
    * **GNPy (PCE):** Motor de cálculo físico que expone una API REST para validar OSNR/GSNR antes del aprovisionamiento.
2. **Emulación de Red (Mininet-Optical):**
    * Instalado en un entorno virtual (venv) para preservar la integridad del sistema.
    * Emula ROADMs Lumentum y tramos de fibra G.652.
    * Utiliza agentes NETCONF para comunicarse con el controlador.
3. **Lógica de Integración (Python Bridge):**
    * Script que actúa como orquestador de servicios, consultando a GNPy y ordenando a ONOS la instalación de flujos.

## Estado de Instalación y Rutas Clave

* **Python Venv:** `~/optical-lab-env`
* **Intérprete para Mininet:** `sudo ~/optical-lab-env/bin/python3`
* **Acceso a ONOS:** `localhost:30181` (GUI) / `localhost:30101` (CLI - SSH).
* **Acceso a GNPy:** `http://localhost:8080` (vía port-forward de K3s).

## Flujo Operativo (Workflow)

1. **Definición:** Se carga la topología física en `topology.json`.
2. **Validación:** El agente consulta a la API de GNPy la viabilidad de un canal (ej: 16-QAM entre Río Cuarto y Córdoba).
3. **Aprovisionamiento:** Si la OSNR es > 15dB, ONOS configura los cross-connects en los ROADMs de Mininet-Optical.

## Notas Técnicas para el Agente

* **Fibras:** Se asumen coeficientes de pérdida de 0.22 dB/km.
* **ROADMs:** Tipo Lumentum Whitebox (modelo de datos OpenConfig).
* **Protocolos:** NETCONF para configuración de hardware, REST para comunicación entre servicios.

## Objetivos Próximos

- [x] Implementar redundancia de ruta automática ante cortes de enlace en Mininet.
* [ ] Integrar hardware físico (Mikrotik hAP/mAP) para la gestión del plano de control fuera de banda.
* [ ] Documentar el rendimiento de diferentes formatos de modulación según la distancia.

---
*Mantenido por Ramiro Tizzian - Estudiante de Ingenieria en telecomunicaciones
