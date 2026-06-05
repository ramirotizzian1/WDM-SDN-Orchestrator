estamos hablando de integrar el ecosistema ODTN (Optical Disaggregated Transport Network).

Esta arquitectura permite separar el hardware (ROADMs) del software de control,
utilizando modelos de datos estándar como OpenConfig.

Arquitectura General del Sistema
La solución se divide en tres capas funcionales, todas orquestadas dentro de un clúster de Kubernetes (K8s) para garantizar escalabilidad y aislamiento.

 1. **Capa de Datos Emulada (Mininet-Optical)**  
Mininet-Optical extiende Mininet para soportar elementos WDM.

Nodos ROADM: Se modelan como agentes que exponen interfaces NETCONF siguiendo el modelo de Lumentum (OpenConfig).

Terminales (Transponders): Generan las señales ópticas con parámetros ajustables (frecuencia, potencia, modulación).

Fibras y Amplificadores: Mininet-Optical emula la atenuación y ganancia, pero delega el cálculo complejo de ruido a GNPy.

**Flujo de Trabajo (Workflow)**

1. Aprovisionamiento: El usuario solicita una conexión de 100G entre el Nodo A y el Nodo C.

2. Cálculo de Ruta: ONOS identifica los saltos físicos.

3. Simulación Física: GNPy recibe la topología y estima si la señal llegará con suficiente calidad al receptor tras pasar por los ROADMs y amplificadores.

4. Configuración: Si el resultado es positivo, ONOS configura los ROADMs en Mininet-Optical vía NETCONF/OpenConfig.

**Componentes clave para tu implementación:**
Mininet-Optical: Debes usar la rama que soporta REST o NETCONF agents para que ONOS pueda interactuar con los nodos como si fueran equipos reales.

Configuración de GNPy: Necesitarás un archivo network_topology.json que describa los parámetros de los ROADMs Lumentum (pérdidas de inserción, figuras de ruido de amplificadores internos).

Driver de ONOS: Asegúrate de activar los drivers lumentum-netconf o optical-rest dentro de ONOS para que reconozca el modelo de datos de los agentes emulados.

---
Con quien se comunica gnpy para saber la viabilidad del enlace optico para que el onos pueda configurar los roadms en mininet-optical.

---

### Limitaciones Conocidas del Entorno (Troubleshooting) y Soluciones

**Problema 1: ONOS no descubría los puertos de los ROADM**
**Causa:** El servidor Netconf emulado (`mnoptical/ofcdemo/netconfserver.py`) venía con la función `add_ports()` comentada de fábrica.
**Solución Aplicada:** Se implementó manualmente el código XML de la función para reportar los puertos físicos (Mux Input, Demux Output, Line In, Line Out). Tras el parche, ONOS descubre y registra exitosamente los puertos (4101, 5201, 4201, 5101) bajo el protocolo NETCONF.

**Problema 2: ONOS no dibuja los enlaces ópticos y los Intents fallan**
**Causa:** Aunque los puertos existen, el motor estático de ONOS (`netcfglinksprovider`) suele rechazar la instanciación visual de enlaces ópticos unidireccionales genéricos entre puertos de tipo OCh (Optical Channel) si no son inyectados mediante TAPI y el subsistema ODTN. 
Como consecuencia, si se intenta usar un `PointToPointIntent` (que espera enlaces lógicos en el grafo), ONOS lo marca como `FAILED` porque el servicio de rutas no ve los enlaces.

**Solución Estratégica (Bypass del Intent Compiler):**
En lugar de depender de los *Intents* (que requieren que ONOS calcule la ruta sobre un grafo perfecto), la lógica de enrutamiento se delegó completamente al orquestador en Python (`bridge_agent.py`), quien:
1. Lee la topología real (`topology.json`).
2. Verifica la viabilidad con GNPy.
3. Envía instrucciones directas a nivel de hardware (usando **FlowRules**) a la API REST de ONOS (`POST /onos/v1/flows`).

Con este enfoque, ONOS recibe la orden con un selector óptico (`OCH_SIGID` encapsulando el `gridType` DWDM y el canal), lo traduce al modelo Lumentum y lo inyecta mediante NETCONF en los ROADMs de Mininet-Optical. El tráfico se encamina de forma exitosa y soporta redundancia, logrando el aprovisionamiento SDN completo.

---

### Fase 2 (Trabajo Futuro): Arquitectura Carrier-Class (Docker + OpenConfig)

Como evolución natural del proyecto, se ha diseñado una transición para superar las limitaciones de `mininet-optical` y aprovechar al 100% los motores ópticos internos de ONOS (como el *Intent Framework* y la autogeneración de TAPI).

**El Nuevo Paradigma:**
En lugar de un script monolítico de emulación, la Fase 2 propone utilizar contenedores Docker individuales para cada ROADM. 
Los archivos de configuración inicial para esta fase se encuentran en la carpeta `docker-openconfig-emulator/`.

1. **El Motor NETCONF (Netopeer2 + Sysrepo):** Cada contenedor ejecuta un servidor NETCONF completo respaldado por una base de datos validada por YANG.
2. **Modelos OpenConfig:** Se inyectan los módulos YANG oficiales del consorcio OpenConfig en los contenedores. Esto hace que ONOS sea incapaz de distinguir entre el simulador y un hardware real Lumentum de grado Carrier.
3. **Mapeo TAPI Automático:** Al leer los modelos OpenConfig perfectos, el driver ODTN de ONOS autogenerará los *TAPI Nodes* y los *Service Interface Points* (SIPs).
71. **Ventaja Principal:** Esto permite deshacerse de los `FlowRules` directos y el orquestador externo para el cálculo de rutas; ONOS asumirá el control nativo del ruteo óptico y la protección (Restoration) de los lightpaths.

* **Resolución del Race Condition (Driver Match):** Se identificó y resolvió el error de `Driver not found`. El problema radicaba en un "Race Condition" durante el arranque de ONOS: la configuración `netcfg-docker.json` se inyectaba milisegundos después de activar la aplicación `odtn-service`, mucho antes de que Karaf finalizara la carga asíncrona de los binarios del `odtn-driver`. ONOS rechazaba el mapeo porque el driver aún no existía en la memoria del controlador.
* **Solución Aplicada:** Se desarrolló un script orquestador (`fix_onos2.sh`) que asegura una pausa controlada de 30 segundos posterior a la activación del servicio ODTN, garantizando el despliegue del driver previo a la inyección de la red.
* **Mapeo Exitoso de Puertos (TRIB y LINE):** Al sincronizar el tiempo de carga e inyectar el driver definitivo (`cassini-openconfig`), ONOS logra parsear el árbol YANG interno de Netopeer2.
* **Visualización:** Todos los 4 contenedores ahora aparecen nativamente en ONOS como nodos `TERMINAL_DEVICE` (reconociendo el hardware EDGECORE Cassini y el software OcNOS). El controlador es capaz de listar de forma perfecta los puertos de cliente (ej: `xe1/1` mapeado como puerto tipo `packet` de 100G) y los puertos ópticos de línea (ej: `oe1/1` mapeado como puerto tipo `och` con modulación `ODU4`). La infraestructura está lista para la autogeneración de servicios TAPI.

#### 5. Enrutamiento y Aprovisionamiento (Fase 2)
* **Intents Estáticos (Opción A):** Se logró registrar con éxito un `OpticalConnectivityIntent` directamente en Karaf CLI y también usando la API TAPI (`POINT_TO_POINT_CONNECTIVITY`). Sin embargo, el compilador de rutas de ONOS marcaba el estado como `FAILED`.
* **Causa del Fallo:** Al tratarse de emuladores WDM puros, no transmiten tramas LLDP. ONOS (`TopologyService`) no puede descubrir los enlaces físicos (fibras) entre los ROADMs, imposibilitando el cálculo automático de rutas (Path Computation).
* **Solución Adoptada (Opción B):** Se actualizó el `bridge_agent.py` para mapear de manera estricta los puertos de la Fase 2 (`1100X` y puertos `101`, `201`, `202`). El script Python actúa como el OLS (Optical Line System), consultando a GNPy e inyectando las *FlowRules* precisas directo a los contenedores Netconf mediante REST, logrando el aprovisionamiento de circuito óptico SDN de forma confiable e idéntica a los switches físicos Carrier-Class.

#### 6. Arquitectura de Enrutamiento Óptico (Capa 0 y 1)
En la Fase 2, la red ya no opera con paquetes IP (Capa 3), sino con **haces de luz láser (lambdas)** en la capa física. El proceso de enrutamiento se divide en tres niveles fundamentales:
1. **El Arquitecto (Inteligencia de Enrutamiento):** El script `bridge_agent.py` conoce la topología física, consulta a GNPy para asegurar la viabilidad de la señal óptica y decide la ruta física exacta que debe tomar la luz. Una vez decidida, envía instrucciones genéricas (`FlowRules`) a ONOS.
2. **El Traductor y Controlador (ONOS):** Actuando como el cerebro SDN, ONOS no calcula la ruta, pero recibe los `FlowRules` y los traduce a comandos sumamente complejos en formato **NETCONF/YANG** (usando los modelos de OpenConfig).
3. **El Hardware (Contenedores Netopeer2/Sysrepo):** Los contenedores Cassini actúan en el plano de datos. Reciben la orden XML de ONOS por el puerto 830 y configuran sus matrices de conmutación (simulando los espejos WSS reales) para dejar fluir la luz desde el puerto de entrada óptica (ej: `201`) hacia el puerto de salida o hacia el cliente (`101`). Con este modelo, las "lambdas" llegan a destino bajo una auténtica arquitectura óptica desglosada (ODTN).
