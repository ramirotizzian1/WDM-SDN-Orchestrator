# Fase 2: Simulador Carrier-Class (Docker + Sysrepo/Netopeer2)

Este directorio contiene la arquitectura propuesta para la **Fase 2** del laboratorio. 
El objetivo es reemplazar `mininet-optical` por un conjunto de contenedores Docker individuales, cada uno ejecutando un servidor NETCONF completo (Netopeer2) respaldado por los modelos de datos YANG oficiales de **OpenConfig** y **ODTN**.

## ¿Por qué esta transición?
1. **Integración Perfecta con ONOS:** Al responder exactamente como un equipo real, ONOS autogenerará la topología TAPI y activará sus motores de ruteo y validación de lambdas (OpticalResourceService).
2. **Uso de Intents Nativos:** Podremos dejar de inyectar FlowRules manuales y usar el `OpticalConnectivityIntent`.
3. **Escalabilidad:** Separar los nodos en contenedores permite simular latencias, fallas de red y aprovisionamiento distribuido.

## Pasos para la Implementación (Trabajo Futuro):
1. Escribir un `Dockerfile` que parta de `sysrepo/sysrepo-netopeer2` y ejecute `sysrepoctl -i` para cargar los archivos `.yang` de `openconfig-platform` y `openconfig-terminal-device`.
2. Crear un archivo `init-config.xml` para cargar el estado inicial de cada ROADM (declarar los puertos físicos) usando `sysrepocfg`.
3. Levantar la red con `docker-compose up -d`.
4. Actualizar el `netcfg.json` principal de ONOS para usar la IP de los contenedores y el driver `odtn-terminal-device`.
5. Usar la API TAPI de ONOS para inyectar los enlaces de fibra entre los *NodeEdgePoints* generados automáticamente.
