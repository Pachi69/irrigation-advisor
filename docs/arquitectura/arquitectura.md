# Arquitectura del sistema — irrigation-advisor

## Stack tecnológico

| Capa | Tecnología | Justificación |
|---|---|---|
| Backend | FastAPI + Python | Liviano, tipado, ideal para APIs y procesamiento científico |
| Base de datos | PostgreSQL | Soporte de datos relacionales y geoespaciales |
| Procesamiento satelital | Google Earth Engine (Python client) | Acceso a Sentinel-2 sin infraestructura propia |
| Datos climáticos | Open-Meteo API (primaria) + NASA POWER (fallback) | Gratuitos, sin credenciales; Open-Meteo sirve modelos ECMWF/ERA5 y calcula ETo FAO-56. Detalle en sección "Fuentes de datos climáticos". |
| Jobs automáticos | APScheduler | Job diario (22hs) + job de alertas (cada 6hs) |
| Frontend | Vue 3 + Vite (PWA) | Liviano, rápido de desarrollar, soporte PWA nativo |
| Notificaciones | Web Push (VAPID) | Estándar PWA, sin costo, sin dependencia de terceros |
| Deploy | Railway | Simple, económico, soporte de monorepo |

---

## Componentes del sistema

### Fuentes de datos externas
- **Google Earth Engine**: extracción de NDVI promedio sobre el polígono del campo usando imágenes Sentinel-2 (10m/pixel).
- **Open-Meteo API**: datos climáticos actuales y pronóstico a 5 días (temperatura, humedad, viento, radiación, precipitación y probabilidad de precipitación). También disponible ETo calculada para validación cruzada.

### Backend (FastAPI)
Módulos internos:

| Módulo | Responsabilidad |
|---|---|
| `ingesta/` | Conexión a GEE y Open-Meteo, validación y limpieza de datos |
| `calculo/` | ETo Penman-Monteith (FAO-56), Kc dinámico desde NDVI, balance hídrico |
| `decision/` | Índice de urgencia, ajuste por pronóstico, generación de alertas |
| `api/` | Endpoints REST consumidos por la PWA |
| `jobs/` | Job diario de recomendación (22hs) y job de alertas climáticas (cada 6hs) |
| `auth/` | Registro, login, JWT, roles (productor / admin) |

### Base de datos (PostgreSQL)
Entidades principales: `productor`, `campo`, `suelo`, `recomendacion`, `alerta`.
El polígono del campo se almacena como GeoJSON y es asignado por el admin al momento de aprobar el campo.

### Frontend (PWA — Vue 3 + Vite)
Pantallas principales:
- Login / registro (estado pendiente de aprobación)
- Recomendación del día con nivel de urgencia y razón
- Historial de recomendaciones anteriores
- Estado general del cultivo

### Notificaciones push
Implementadas con el estándar Web Push (VAPID). Se envían desde el backend en dos contextos:
- **Recomendación diaria**: generada por el job nocturno.
- **Alertas climáticas**: generadas por el job cada 6hs ante condiciones críticas (granizo, helada, ola de calor).

---

## Estructura del monorepo

```
irrigation-advisor/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── calculo/
│   │   ├── ingesta/
│   │   ├── decision/
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
| V. Build, release, run | Pipeline separado: build de la PWA, build del backend, deploy en Railway |
| VI. Processes | Backend stateless. El estado persiste únicamente en PostgreSQL |
| VII. Port binding | FastAPI expone el servicio vía puerto configurado por variable de entorno |
| VIII. Concurrency | Jobs independientes del proceso web principal (APScheduler) |
| IX. Disposability | Arranque rápido, shutdown graceful en FastAPI |
| X. Dev/prod parity | Docker para mantener paridad entre entorno local y producción |
| XI. Logs | Logs a stdout (sin archivos), Railway los captura y centraliza |
| XII. Admin processes | Scripts de administración (migraciones, carga inicial) como procesos independientes |

---

## Decisiones técnicas relevantes

- **Kc dinámico con fallback tabular**: el Kc se calcula desde NDVI cuando hay imagen disponible. Si GEE no retorna datos (nubosidad, malla antigranizo), se usa Kc tabular por etapa fenológica del cultivo.
- **Polígono asignado por admin**: el productor registra su campo con datos básicos. El admin aprueba y asigna el polígono GeoJSON. Esto garantiza calidad del área de análisis satelital.
- **Buffer negativo en polígono**: al procesar en GEE se aplica un buffer negativo de ~20m para evitar píxeles mixtos en los bordes del campo.

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
- Sin credenciales ni API key (compatible con deploy simple en Railway).
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
