# Modelo de datos — irrigation-advisor

## Diagrama Entidad-Relación

```mermaid
erDiagram
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
        enum cultivo "vid | durazno | alfalfa"
        float superficie_ha
        enum tipo_riego "goteo | aspersion | surco"
        enum tipo_suelo "arenoso | franco | arcilloso"
        enum estado "pendiente | activo | inactivo"
        json poligono_geojson
        float elevacion_msnm
        float latitud
        float longitud
        bool tiene_malla_antigranizo
        date fecha_siembra_brotacion
        float ultimo_deficit_mm
        date ultima_fecha_deficit
        timestamp created_at
    }

    suelo {
        int id PK
        int campo_id FK
        float capacidad_campo "FC m3/m3"
        float punto_marchitez "WP m3/m3"
        float densidad_aparente "kg/m3"
        timestamp created_at
    }

    registro_satelital {
        int id PK
        int campo_id FK
        date fecha
        enum fuente "sentinel2 | planet"
        float ndvi
        float nubosidad_pct
        bool evento_humedad_detectado
        timestamp created_at
    }

    recomendacion {
        int id PK
        int campo_id FK
        date fecha
        float eto_mm
        float kc
        enum kc_fuente "planet_dinamico | s2_dinamico | tabular"
        float etc_mm
        float deficit_hidrico_mm "Dr acumulado"
        float ks "coef. estres hidrico 0-1"
        float taw_mm "agua total disponible mm"
        float raw_mm "agua facilmente disponible mm"
        float ndvi "valor usado para calcular Kc"
        date fecha_ndvi "fecha de la imagen satelital usada"
        enum etapa_fenologica "inicial | desarrollo | media | final"
        float lamina_recomendada_mm
        enum urgencia "baja | media | alta | critica"
        text razon
        float precipitacion_mm
        enum confianza "alta | media | baja"
        timestamp created_at
    }

    confirmacion_riego {
        int id PK
        int recomendacion_id FK
        int campo_id FK
        date fecha_riego
        float lamina_aplicada_mm
        timestamp created_at
    }

    alerta {
        int id PK
        int campo_id FK
        enum tipo "helada | granizo | ola_calor | deficit_critico"
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

    usuario       ||--o{ campo              : "tiene"
    campo         ||--||  suelo             : "tiene"
    campo         ||--o{ registro_satelital : "genera"
    campo         ||--o{ recomendacion      : "recibe"
    campo         ||--o{ alerta             : "genera"
    recomendacion ||--o| confirmacion_riego : "confirma"
    usuario       ||--o{ suscripcion_push   : "registra"
```

---

## Decisiones de diseño

### Lo que va en la base de datos
- Parámetros de suelo (FC, WP, densidad) se derivan del `tipo_suelo` del campo usando tablas FAO estáticas al momento de activar el campo. Se guardan en `suelo` para no recalcular.
- El `ultimo_deficit_mm` y `ultima_fecha_deficit` del campo permiten el backfill retroactivo del balance hídrico ante días sin recomendación guardada.
- `registro_satelital` unifica registros de distintas fuentes satelitales (Planet Labs y Sentinel-2) en una sola tabla, identificadas por el campo `fuente`.
- `ndvi` y `fecha_ndvi` en `recomendacion` registran qué imagen satelital se usó para calcular el Kc de ese día.

### Lo que NO va en la base de datos (configuración estática en código)
- Kc por etapa fenológica para cada cultivo
- Duración de cada etapa fenológica por cultivo
- Profundidad de raíces (Zr) por etapa por cultivo
- Fracción de depleción permisible (p) por cultivo
- Valores FC/WP/densidad por tipo de suelo
- Umbrales de alerta climática (temperatura de helada, etc.)

### Flujo de confianza de Kc
| Situación | kc_fuente | confianza |
|---|---|---|
| Planet Labs disponible, nubosidad baja | planet_dinamico | alta |
| Sin imagen Planet, Sentinel-2 disponible, nubosidad baja | s2_dinamico | alta |
| Imagen disponible pero campo con malla antigranizo | tabular | media |
| Sin imagen de ninguna fuente satelital | tabular | media |
