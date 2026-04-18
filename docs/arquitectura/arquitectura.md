# Arquitectura del sistema — irrigation-advisor

## Stack tecnológico

| Capa | Tecnología | Justificación |
|---|---|---|
| Backend | FastAPI + Python | Liviano, tipado, ideal para APIs y procesamiento científico |
| Base de datos | PostgreSQL | Soporte de datos relacionales y geoespaciales |
| Procesamiento satelital | Google Earth Engine (Python client) | Acceso a Sentinel-2 sin infraestructura propia |
| Datos climáticos | Open-Meteo API | Gratuito, cubre Argentina, pronóstico a 7 días |
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
- **Open-Meteo como fuente única de clima**: cubre Mendoza con datos horarios, no requiere API key y ofrece ETo precalculada útil para validación cruzada del motor propio.
