# Modelo de datos — irrigation-advisor

> Modelo objetivo del Sprint 2 (introducción de `sector`). El detalle de diseño, jobs y
> plan de implementación está en `docs/diseno/sprint-2-sectores.md`.

## Diagrama Entidad-Relación

```mermaid
erDiagram
    usuario ||--o{ campo : tiene
    campo   ||--o{ sector : contiene
    sector  ||--o{ registro_satelital : genera
    sector  ||--o{ balance_hidrico_diario : calcula
    balance_hidrico_diario ||--o| recomendacion : genera
    recomendacion ||--o| confirmacion_riego : confirma
    sector  ||--o{ confirmacion_riego : registra
    campo   ||--o{ alerta : genera
    usuario ||--o{ suscripcion_push : registra

    usuario {
        int id PK
        string nombre
        string email
        string password_hash
        enum rol "productor | admin"
        bool activo
        timestamp created_at
    }

    campo {
        int id PK
        int usuario_id FK
        string nombre
        enum tipo_suelo "12 clases texturales USDA (sand..clay)"
        enum estado "pendiente | activo | inactivo"
        float latitud "centroide de la union de sectores"
        float longitud
        float elevacion_msnm
        timestamp created_at
    }

    sector {
        int id PK
        int campo_id FK
        string nombre
        enum cultivo "vid | durazno"
        string variedad "ej. Malbec / base champagne"
        float superficie_ha
        json poligono_geojson
        enum tipo_riego "aspersion | superficial"
        float dotacion_ls_ha "L/s/ha (default 1.5)"
        float eficiencia "0-1 (default 0.8 asp / 0.6 sup)"
        enum tipo_malla "ninguna | abierta | densa | color"
        int frecuencia_notif_dias "cada cuanto notificar"
        time hora_notif "hora elegida para notificar"
        date ultima_notif_fecha "control de frecuencia"
        date ultima_fecha_saturacion
        float ultimo_deficit_mm
        date ultima_fecha_deficit
        timestamp created_at
    }

    registro_satelital {
        int id PK
        int sector_id FK
        date fecha
        float ndvi
        float nubosidad_pct
        bytes thumbnail_png "overlay NDVI para el mapa"
        timestamp created_at
    }

    balance_hidrico_diario {
        int id PK
        int sector_id FK
        date fecha
        float eto_mm
        float kc
        enum kc_fuente "s2_dinamico | tabular"
        float etc_mm
        float deficit_hidrico_mm "Dr acumulado"
        float ks "coef. estres hidrico 0-1"
        enum etapa_fenologica "inicial | desarrollo | media | tardia | reposo"
        float precipitacion_mm
        float taw_mm "agua total disponible mm"
        float raw_mm "agua facilmente disponible mm"
        float ndvi "valor usado para calcular Kc"
        date fecha_ndvi "fecha de la imagen satelital usada"
        timestamp created_at
    }

    recomendacion {
        int id PK
        int balance_id FK "1:1 con balance_hidrico_diario"
        float lamina_recomendada_mm
        float volumen_m3 "persistido, inmutable"
        float tiempo_min "persistido, inmutable"
        enum urgencia "baja | media | alta | critica"
        text razon
        enum confianza "alta | media | baja"
        timestamp created_at
    }

    confirmacion_riego {
        int id PK
        int recomendacion_id FK
        int sector_id FK
        date fecha_riego
        float lamina_aplicada_mm "normalizada desde mm / m3 / tiempo"
        timestamp created_at
    }

    alerta {
        int id PK
        int campo_id FK
        enum tipo "helada | ola_calor"
        text mensaje
        date fecha
        bool enviada
        timestamp created_at
    }

    suscripcion_push {
        int id PK
        int usuario_id FK
        text endpoint
        string p256dh
        string auth
        timestamp created_at
    }
```

---

## Decisiones de diseño

### Jerarquía campo → sector
- `campo` es el **contenedor** (un dueño, una ubicación para el clima, un tipo de suelo).
- `sector` es la unidad de cálculo: cada sector tiene su **variedad**, **polígono**, **tipo de riego** y se le calcula NDVI, balance y recomendación de forma independiente.
- Un campo tiene **≥ 1 sector**.
- `latitud`/`longitud` del campo se derivan del **centroide de la unión de los polígonos de sus sectores**; con ese punto se consultan SoilGrids (tipo de suelo) y la elevación.

### Lo que va en la base de datos
- Parámetros de suelo (FC, WP) se derivan del `tipo_suelo` del **campo** usando la tabla de Saxton & Rawls (2006) para las 12 clases texturales USDA.
- El `ultimo_deficit_mm` y `ultima_fecha_deficit` del **sector** permiten el backfill retroactivo del balance hídrico ante días sin recomendación guardada.
- `registro_satelital` guarda los registros de NDVI (Sentinel-2 vía GEE) por **sector** y fecha, con el thumbnail PNG que la PWA muestra como overlay; funciona además como **cache** de NDVI.
- `balance_hidrico_diario` guarda el estado hídrico de cada día por sector; `recomendacion` se relaciona 1:1 y guarda la salida para el productor (lámina mm, **volumen m³**, **tiempo min**, urgencia, razón, confianza).
- `volumen_m3` y `tiempo_min` se persisten al generar la recomendación (inmutables); fórmulas en `docs/referencias/referencias.md`.

### Lo que NO va en la base de datos (configuración estática en código)
- Kc por etapa fenológica, duración de etapas, profundidad de raíces (Zr) y fracción de depleción (p) por cultivo.
- Valores FC/WP por tipo de suelo (Saxton & Rawls 2006).
- Umbrales de alerta climática (temperatura de helada, etc.).

### Flujo de confianza de Kc (según malla del sector)
| Situación del sector | kc_fuente | confianza |
|---|---|---|
| Sentinel-2 nítida, sin malla (`ninguna`) | s2_dinamico | alta |
| Sentinel-2 nítida, malla `abierta` | s2_dinamico | media |
| Malla `densa` o `color` | tabular | media |
| Sin imagen óptica reciente (nublado) | tabular | media |
