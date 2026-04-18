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
        enum tipo_riego "inundacion | goteo | aspersion"
        enum tipo_suelo "arenoso | franco | arcilloso"
        enum estado "pendiente | activo | inactivo"
        json poligono_geojson
        float elevacion_msnm
        float latitud
        float longitud
        bool tiene_malla_antigranizo
        date fecha_siembra_brotacion
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
        enum fuente "sentinel2 | sentinel1"
        float ndvi "null si fuente=sentinel1"
        float ndwi "null si fuente=sentinel1"
        float evi "null si fuente=sentinel1"
        float backscatter_vv "null si fuente=sentinel2"
        float backscatter_vh "null si fuente=sentinel2"
        float nubosidad_pct "null si fuente=sentinel1"
        bool evento_humedad_detectado
        timestamp created_at
    }

    recomendacion {
        int id PK
        int campo_id FK
        date fecha
        float eto_mm
        float kc
        enum kc_fuente "s2_dinamico | tabular"
        float etc_mm
        float deficit_hidrico_mm "Dr acumulado"
        float ks "coef. estres hidrico 0-1"
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

    usuario      ||--o{ campo              : "tiene"
    campo        ||--||  suelo             : "tiene"
    campo        ||--o{ registro_satelital : "genera"
    campo        ||--o{ recomendacion      : "recibe"
    campo        ||--o{ alerta             : "genera"
    recomendacion ||--o| confirmacion_riego : "confirma"
```

---

## Decisiones de diseño

### Lo que va en la base de datos
- Parámetros de suelo (FC, WP, densidad) se derivan del `tipo_suelo` del campo usando tablas FAO estáticas al momento de activar el campo. Se guardan en `suelo` para no recalcular.
- El `deficit_hidrico_mm` de la última `recomendacion` es el punto de partida del balance del día siguiente.
- `registro_satelital` unifica datos de Sentinel-2 (NDVI/NDWI/EVI) y Sentinel-1 (backscatter + detección de humedad) en una sola tabla.

### Lo que NO va en la base de datos (configuración estática en YAML)
- Kc por etapa fenológica para cada cultivo
- Duración de cada etapa fenológica por cultivo
- Profundidad de raíces (Zr) por etapa por cultivo
- Fracción de depleción permisible (p) por cultivo
- Valores FC/WP/densidad por tipo de suelo
- Umbrales de alerta climática (temperatura de helada, etc.)

### Flujo de confianza de Kc
| Situación | kc_fuente | confianza |
|---|---|---|
| Sentinel-2 disponible, nubosidad baja, sin malla | s2_dinamico | alta |
| Sentinel-2 muy nublada | tabular | media |
| Campo con malla antigranizo | tabular | media |
