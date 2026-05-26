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
        enum cultivo "vid | durazno"
        float superficie_ha
        enum tipo_suelo "12 clases texturales USDA (sand..clay)"
        enum estado "pendiente | activo | inactivo"
        json poligono_geojson
        float elevacion_msnm
        float latitud
        float longitud
        bool tiene_malla_antigranizo
        date ultima_fecha_saturacion
        float ultimo_deficit_mm
        date ultima_fecha_deficit
        timestamp created_at
    }

    registro_satelital {
        int id PK
        int campo_id FK
        date fecha
        float ndvi
        float nubosidad_pct
        bytes thumbnail_png "overlay NDVI para el mapa"
        timestamp created_at
    }

    balance_hidrico_diario {
        int id PK
        int campo_id FK
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
        enum urgencia "baja | media | alta | critica"
        text razon
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

    usuario                ||--o{ campo                  : "tiene"
    campo                  ||--o{ registro_satelital     : "genera"
    campo                  ||--o{ balance_hidrico_diario : "calcula"
    balance_hidrico_diario ||--o| recomendacion          : "genera"
    campo                  ||--o{ alerta                 : "genera"
    recomendacion          ||--o| confirmacion_riego     : "confirma"
    usuario                ||--o{ suscripcion_push       : "registra"
```

---

## Decisiones de diseño

### Lo que va en la base de datos
- Parámetros de suelo (FC, WP) se derivan del `tipo_suelo` del campo usando la tabla de Saxton & Rawls (2006) para las 12 clases texturales USDA.
- El `ultimo_deficit_mm` y `ultima_fecha_deficit` del campo permiten el backfill retroactivo del balance hídrico ante días sin recomendación guardada.
- `registro_satelital` guarda los registros de NDVI extraídos de Sentinel-2 (vía Google Earth Engine) para cada campo y fecha, junto con el thumbnail PNG que la PWA muestra como overlay sobre el mapa.
- `balance_hidrico_diario` guarda el estado hídrico de cada día (ETo, Kc, Dr, Ks, etapa); `recomendacion` se relaciona 1:1 y guarda solo la salida para el productor (lámina, urgencia, razón, confianza).
- `ndvi` y `fecha_ndvi` en `balance_hidrico_diario` registran qué imagen satelital se usó para calcular el Kc de ese día.

### Lo que NO va en la base de datos (configuración estática en código)
- Kc por etapa fenológica para cada cultivo
- Duración de cada etapa fenológica por cultivo
- Profundidad de raíces (Zr) por etapa por cultivo
- Fracción de depleción permisible (p) por cultivo
- Valores FC/WP por tipo de suelo (Saxton & Rawls 2006)
- Umbrales de alerta climática (temperatura de helada, etc.)

### Flujo de confianza de Kc
| Situación | kc_fuente | confianza |
|---|---|---|
| Sentinel-2 disponible, nubosidad baja | s2_dinamico | alta |
| Imagen disponible pero campo con malla antigranizo | tabular | media |
| Sin imagen óptica reciente (nublado) | tabular | media |
