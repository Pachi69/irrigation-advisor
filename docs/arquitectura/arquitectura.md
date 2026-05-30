# Arquitectura del sistema — irrigation-advisor

## Stack tecnológico

| Capa | Tecnología | Justificación |
|---|---|---|
| Backend | FastAPI + Python | Liviano, tipado, ideal para APIs y procesamiento científico |
| Base de datos | PostgreSQL | Soporte de datos relacionales y geoespaciales |
| Procesamiento satelital | Google Earth Engine (Sentinel-2) | Sentinel-2 SR Harmonizado, 10m/pixel, cada 5–15 días. Autenticación via cuenta de servicio GEE. |
| Datos de suelo | SoilGrids 2.0 (ISRIC) | API REST gratuita (CC-BY 4.0). Devuelve fracciones arena/limo/arcilla en g/kg a 250m. Sin credenciales requeridas. |
| Datos climáticos | Open-Meteo API (primaria) + NASA POWER (fallback) | Gratuitos, sin credenciales; Open-Meteo sirve modelos ECMWF/ERA5 y calcula ETo FAO-56. Detalle en sección "Fuentes de datos climáticos". |
| Jobs automáticos | APScheduler | Job de cálculo (madrugada, batch por sector) + job de notificación (ventana ~15–30 min, por hora/frecuencia de sector) + job de alertas climáticas (cada 6hs) |
| Frontend | Vue 3 + Vite (PWA) | Liviano, rápido de desarrollar, soporte PWA nativo |
| Notificaciones | Web Push (VAPID) | Estándar PWA, sin costo, sin dependencia de terceros |
| Deploy | UM-Cloud (Docker) | Contenerización de backend y frontend sobre infraestructura de la universidad |

---

## Componentes del sistema

### Fuentes de datos externas
- **Google Earth Engine — Sentinel-2 (fuente primaria NDVI)**: extracción de NDVI promedio sobre el polígono del campo. Sentinel-2 SR Harmonizado, 10m/pixel, frecuencia 5–15 días según nubosidad. Se aplica buffer negativo de ~1m para evitar píxeles mixtos. Fallback a Kc tabular FAO-56 cuando no hay imagen clara disponible en los últimos 30 días.
- **SoilGrids 2.0 (ISRIC)**: consulta REST por coordenadas del campo para determinar tipo de suelo automáticamente. Retorna fracciones de arena, limo y arcilla (g/kg) que se clasifican según el triángulo USDA y se mapean al enum `SoilType` del sistema.
- **Open-Meteo API**: datos climáticos actuales y pronóstico a 5 días (temperatura, humedad, viento, radiación, precipitación y probabilidad de precipitación). También disponible ETo calculada para validación cruzada.

### Backend (FastAPI)
Módulos internos:

| Módulo | Responsabilidad |
|---|---|
| `ingestion/` | Conexión a GEE y Open-Meteo (clima 1× por campo, NDVI cacheado por sector), validación y limpieza de datos |
| `calculation/` | ETo Penman-Monteith (FAO-56), Kc dinámico desde NDVI, balance hídrico por sector, conversión lámina↔m³↔tiempo (estrategia por `tipo_riego`) |
| `decision/` | Índice de urgencia, ajuste por pronóstico, confianza de Kc según malla, generación de alertas |
| `services/` | Orquestación de campo/sector (alta, centroide, soil/elevación) y recomendación por sector |
| `api/` | Endpoints REST consumidos por la PWA |
| `jobs/` | Job de cálculo (madrugada, batch por sector), job de notificación (ventana ~15–30 min, por hora/frecuencia de sector) y alertas climáticas (cada 6hs) |
| `auth/` | Registro, login, JWT, roles (productor / admin) |

### Base de datos (PostgreSQL)
Entidades principales: `usuario`, `campo`, `sector`, `registro_satelital`, `balance_hidrico_diario`, `recomendacion`, `confirmacion_riego`, `alerta`, `suscripcion_push`. Detalle completo en `docs/modelo-datos/er-diagram.md`.
- `campo` es el contenedor (un dueño, ubicación para clima, tipo de suelo); `sector` es la unidad de cálculo (variedad, polígono, tipo de riego, malla → NDVI/balance/recomendación independientes).
- **No existe tabla `suelo`**: FC/WP se derivan en runtime del `tipo_suelo` del campo (Saxton & Rawls 2006).
- El polígono lo dibuja el productor **por sector** (GeoJSON); el admin revisa/ajusta antes de aprobar el campo. El `lat/lon` del campo se deriva del centroide de la unión de los sectores.

### Frontend (PWA — Vue 3 + Vite)
Pantallas principales:
- Login / registro (estado pendiente de aprobación)
- Recomendación del día con nivel de urgencia y razón
- Historial de recomendaciones anteriores
- Estado general del cultivo

### Notificaciones push
Implementadas con el estándar Web Push (VAPID). El **cálculo está desacoplado de la notificación**:
- **Cálculo (job de madrugada, batch por sector)**: genera y persiste balance + recomendación de cada sector. No depende de la hora del productor.
- **Notificación de recomendación (job cada ~15–30 min)**: revisa los sectores cuya `hora_notif` cae en la ventana y cuya `frecuencia_notif_dias` ya se cumplió; envía push **solo si la lámina recomendada > 0** (si es 0, la recomendación igual queda registrada). A cada tick solo hace `SELECT` + push → liviano aunque muchos usuarios compartan horario.
- **Alertas climáticas (job cada 6hs)**: condiciones críticas a nivel campo (helada, ola de calor); se envían siempre.

---

## Estructura del monorepo

```
irrigation-advisor/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── calculation/
│   │   ├── ingestion/
│   │   ├── decision/
│   │   ├── services/
│   │   ├── jobs/
│   │   ├── auth/
│   │   └── models/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   ├── components/
│   │   └── services/
│   ├── public/
│   │   └── manifest.json
│   └── package.json
├── docs/
│   └── arquitectura/
│       └── arquitectura.md  ← este archivo
└── README.md
```

---

## Principios de diseño — The Twelve-Factor App

| Factor | Aplicación en este proyecto |
|---|---|
| I. Codebase | Un único repositorio Git (monorepo) para backend y frontend |
| II. Dependencies | `requirements.txt` (Python) y `package.json` (Node) declaran todas las dependencias explícitamente |
| III. Config | Variables de entorno via `.env` (nunca en el código). Incluye claves GEE, configuración de BD, claves VAPID |
| IV. Backing services | PostgreSQL y Open-Meteo tratados como recursos adjuntos, configurables por variable de entorno |
| V. Build, release, run | Pipeline separado: build de la PWA, build del backend, deploy en UM-Cloud (Docker) |
| VI. Processes | Backend stateless. El estado persiste únicamente en PostgreSQL |
| VII. Port binding | FastAPI expone el servicio vía puerto configurado por variable de entorno |
| VIII. Concurrency | Jobs independientes del proceso web principal (APScheduler) |
| IX. Disposability | Arranque rápido, shutdown graceful en FastAPI |
| X. Dev/prod parity | Docker para mantener paridad entre entorno local y producción |
| XI. Logs | Logs a stdout (sin archivos), capturados por el runtime de contenedores (Docker) |
| XII. Admin processes | Scripts de administración (migraciones, carga inicial) como procesos independientes |

---

## Decisiones técnicas relevantes

- **Kc dinámico con fallback**: el Kc se calcula desde NDVI cuando hay imagen disponible. Fuente única: GEE/Sentinel-2 (cada 5–15 días, 10m). Fallback: Kc tabular FAO-56 por etapa fenológica cuando no hay imagen disponible o la nubosidad supera el 20%.
- **Tipo de suelo automático desde SoilGrids**: al crear un campo, se consulta la API SoilGrids con las coordenadas del centroide para determinar el tipo de suelo (clasificación textural USDA, 12 clases) sin intervención del productor. Si la API falla, el sistema solicita selección manual como fallback.
- **Polígono dibujado por el productor**: al registrar el campo, el productor dibuja el polígono de su parcela en un mapa interactivo (Leaflet + Geoman). El admin lo revisa y ajusta si es necesario antes de aprobar. Un productor no puede tener más de un campo pendiente a la vez.
- **Buffer negativo en polígono**: al procesar en GEE se aplica un buffer negativo de ~1m para evitar píxeles mixtos en los bordes del campo.

---

## Fuentes de datos climáticos

### Decisión

**Open-Meteo** como fuente primaria. **NASA POWER** como fuente secundaria de respaldo ante fallas de la fuente primaria. La integración de datos de estaciones locales (INTA SIGA) queda fuera del sistema operativo y se reserva como referencia metodológica para la validación académica del cálculo de ETo.

### Justificación técnica

Open-Meteo no genera datos meteorológicos propios. Actúa como servicio gratuito sobre modelos de referencia mundial:

- **Pronóstico**: ECMWF IFS a resolución de 9 km — el modelo meteorológico global operativo más preciso disponible.
- **Histórico**: ERA5 y ERA5-Land (Copernicus/ECMWF) a 9 km — el reanálisis climatológico de referencia en la literatura académica.

La validación empírica del producto recae sobre estos modelos subyacentes, ampliamente documentados en literatura peer-reviewed, no sobre el servicio Open-Meteo en sí.

Ventajas operativas específicas para este proyecto:
- Sin credenciales ni API key (compatible con deploy simple en contenedor).
- Cuota gratuita amplia (10 000 llamadas/día) más que suficiente para un MVP.
- Pronóstico disponible hasta 16 días; se consumen 5 para alertas de riego.
- Entrega directamente **ETo FAO-56 precalculada**, lo que permite validar cruzadamente el cálculo propio implementado en el módulo `calculo/`.
- Licencia CC-BY 4.0, compatible con uso académico.

### Alternativas evaluadas y descartadas como primarias

| Fuente | Motivo de descarte |
|---|---|
| NASA POWER | Resolución espacial gruesa (≈55 km en meteorología). Sobreestima ETo en climas áridos (RMSE hasta 1.41 mm/d sin corrección, documentado en Paulo et al., *Agronomy* 2021). Se mantiene como respaldo, no como primaria. |
| ERA5 directo (Copernicus CDS) | Latencia de 5 días en ERA5T — incompatible con recomendación de riego diaria. Requiere además registro y token. |
| SMN Argentina | Sin API REST documentada oficialmente (`ws.smn.gob.ar` es endpoint comunitario no oficial). Cobertura limitada de radiación solar, variable crítica para FAO-56. |
| INTA SIGA | Estaciones relevantes existen cerca de San Rafael (Rama Caída, La Consulta), pero el acceso es vía portal web sin API pública. Integración requiere scraping frágil, incompatible con los requisitos de reproducibilidad del MVP. |
| IANIGLA-CONICET | Red de alta montaña (Aconcagua, Observatorio Andino). Cobertura fuera de la zona agrícola de interés. |

### Estrategia de resiliencia

Ante fallas de Open-Meteo (timeout, 5xx, cuota excedida), el sistema intentará obtener los mismos datos de NASA POWER antes de retornar un error al usuario:

1. Primer intento: Open-Meteo `/v1/forecast` o `/v1/archive` según corresponda.
2. Fallback: NASA POWER (gratuito, sin credenciales, cobertura global).
3. Si ambas fallan: el endpoint retorna 502 con mensaje claro y la recomendación del día queda marcada como `confianza: baja` en el modelo (campo `recomendacion.confianza`).

Se acepta la diferencia de precisión entre ambas fuentes como trade-off aceptable frente a una interrupción total del servicio. Las recomendaciones generadas con datos de fallback deben marcarse explícitamente para el productor.

### Validación académica (sección metodológica de la tesis)

Como respaldo empírico de la elección de fuentes, se realizará una validación única y documentada fuera del sistema operativo:

- Descarga manual de datos diarios de una estación INTA cercana a San Rafael (Rama Caída o La Consulta) desde el portal SIGA, para un período representativo (12 meses).
- Cálculo de ETo FAO-56 usando los datos de las tres fuentes (Open-Meteo, NASA POWER, estación INTA) para el mismo punto-período.
- Reporte de RMSE y MBE de cada fuente contra la estación local como referencia.

Este análisis se documenta en notebook reproducible y se incluye como capítulo de la tesis. No forma parte del pipeline operativo del sistema.
