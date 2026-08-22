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

#### 7. Limitaciones del Hardware Simulado (Fallo de Intents Nativos)
Durante el desarrollo se intentó delegar el 100% de la orquestación a ONOS utilizando su módulo nativo `OpticalConnectivityIntent`, inyectando manualmente la topología de enlaces de fibra óptica en la base de datos del controlador (`NetworkConfig`). Sin embargo, los *Intents* continuaron en estado `FAILED`.

Esta experimentación permitió aislar el verdadero límite de la simulación mediante contenedores *OpenConfig*:
1. **Falta de Reporte Espectral (`LambdaQuery`):** En hardware real (ej: un ROADM Lumentum o Cassini real), el equipo responde a las consultas NETCONF exponiendo su matriz de espectro óptico (ej: "Soporte DWDM 50GHz, 96 canales libres"). 
2. **Fallo del Asignador RSA:** Los contenedores con *Netopeer2*, si bien emulan a la perfección los árboles de configuración YANG para conmutar puertos, carecen de los drivers de hardware subyacentes fotónicos. Al no poder reportarle a ONOS la grilla de lambdas disponibles en la fibra, el `ResourceService` de ONOS no puede asignar recursos de espectro.
3. **Validación del Diseño:** Al faltar el reporte espectral, el compilador de *Intents* se detiene. Esto valida y justifica el uso de la arquitectura **Hierarchical SDN** adoptada (Opción B): delegar la Inteligencia y Asignación de Espectro (RSA) al Orquestador Superior (`bridge_agent.py` + GNPy) y utilizar ONOS exclusivamente como el traductor universal y ejecutor de bajo nivel (`FlowRules`). Esta es exactamente la arquitectura recomendada en implementaciones reales *Carrier-Class* para Redes Ópticas Desglosadas.

#### 8. Implementación del Motor RWA (Routing and Wavelength Assignment) y Control Espectral
Para superar la falta de asignador RSA dentro de ONOS analizada en la sección anterior, se desarrolló un motor de Asignación de Longitud de Onda original en el orquestador Python (`bridge_agent.py`):
1. **Base de Datos de Estado Local (`spectrum_db.json`):** El orquestador mantiene una matriz persistente con los 96 canales de la grilla DWDM de 50GHz para cada enlace bidireccional físico de la red.
2. **Algoritmo *First-Fit*:** Al calcular un nuevo circuito tras una petición (o tras un corte de fibra), la función `find_available_lambda()` realiza una operación matemática de intersección de conjuntos a lo largo de toda la ruta calculada. Esto garantiza matemáticamente el cumplimiento de la **Restricción de Continuidad de Longitud de Onda**, seleccionando y bloqueando automáticamente el primer canal (Lambda) disponible.
3. **Control desde la Capa de Aplicación:** Se expandió la interfaz de usuario (Dashboard React) permitiendo al operador forzar una Lambda específica para un servicio. Si se ingresa la "Lambda 15", el Dashboard se comunica vía API REST con el orquestador, el cual omite el algoritmo automático, bloquea el canal 15 en la base de datos local y propaga la orden WDM a ONOS codificada en el payload `spacingMultiplier=15`.
4. **Prueba Empírica del Emulador:** Durante el desarrollo de este módulo, se auditaron los contenedores `oc-cassini` (Netopeer2) ejecutando el comando de inspección interna `sysrepoctl -l`. Se comprobó que las imágenes de la ONF carecen del módulo `openconfig-terminal-device` necesario para el almacenamiento de parámetros fotónicos. Esto constituyó la prueba empírica definitiva de que los contenedores WDM de esta versión actúan como meros *proxies* lógicos que descartan los valores de frecuencia, re-confirmando que la inteligencia de espectro (OLS) DEBE residir sí o sí en un componente superior (como el `bridge_agent.py`), replicando el estándar Cognitive Optical Network.

#### 9. Multiplexación WDM Real y Liberación Específica de Flujos
Para simular el funcionamiento de un entorno Carrier-Class real, el controlador soporta *Multiplexación WDM*, permitiendo la acumulación de múltiples circuitos en la misma fibra. Adicionalmente, se desarrolló el endpoint `/api/free` el cual:
1. Mapea la petición de liberación a un servicio activo.
2. Consulta la API REST de ONOS (`GET /onos/v1/flows/{deviceId}`) para auditar las reglas configuradas.
3. Busca iterativamente la regla que contiene el selector `OCH_SIGID` con el `spacingMultiplier` correspondiente a la lambda deseada.
4. Envía la orden HTTP DELETE apuntando al `flowId` exacto, eliminando la frecuencia de la memoria del ROADM físico y del plano de datos sin afectar a los demás servicios multiplexados (Traffic Isolation).

#### 10. Modelado de Capa Física Predictiva (QoT) con Formatos de Modulación
Se implementó una simulación predictiva en la función `validate_qot()` de Python para replicar el comportamiento del motor físico (GNPy). El sistema:
1. Lee las distancias físicas (km) entre nodos desde el archivo maestro `topology.json`.
2. Habilita al usuario la selección de formato de modulación óptica en el dashboard (QPSK, 16-QAM, 64-QAM).
3. Evalúa la viabilidad de la OSNR cruzando la longitud total de la ruta calculada contra el umbral máximo de tolerancia del formato (Ej: 64-QAM restringe a 200 km por su alta sensibilidad, mientras que QPSK sobrevive hasta 2000 km).
Si el umbral es violado, la orquestación falla proactivamente evitando caídas en el hardware.

#### 11. Memoria de Estado y Restauración Masiva Ante Fallos
El agente de orquestación cuenta con una memoria persistente (`active_circuits`) de todos los servicios inyectados en ONOS. Al presentarse un corte de fibra:
1. Escanea su memoria e identifica *todos* los circuitos multiplexados que transitaban por el enlace afectado.
2. Des-aprovisiona las reglas obsoletas y ejecuta un *Mass Rerouting* para cada uno de los clientes hacia caminos de contingencia.
3. Al encontrar nuevas rutas, el motor RSA respeta estrictamente la *Wavelength Continuity Constraint* al pasar el parámetro original (`force_lambda=c["lambda"]`), garantizando que el servicio mantenga su "color" óptico (frecuencia) a lo largo del proceso de restauración.
