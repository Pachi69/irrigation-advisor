# Evaluación: simulación de eficiencia hídrica

## Simulación exploratoria (junio de 2026)

Análisis exploratorio previo al protocolo de evaluación. Se versiona sin cambios
respecto de junio de 2026, salvo la ubicación del sector y los datos descargados
en ella, que no se versionan (ver "Ubicación del sector"). No es la simulación
utilizada en la tesis.

Compara, con el mismo balance hídrico FAO-56 del sistema (`app.calculation`), la
política del sistema (riega cuando el agotamiento alcanza RAW y repone a capacidad
de campo) contra calendarios fijos de 7, 10 y 14 días, dosificados al requerimiento
neto estacional o a la misma agua que aplicó el sistema. Usa el clima del
producto por defecto de Open-Meteo (best_match) y el NDVI Sentinel-2 del sector
Malbec en tres temporadas de riego (septiembre a abril, 2021/22 a 2023/24).

| Archivo | Contenido |
|---|---|
| `sim_efficiency.py` | Simulación. Sin argumentos genera `_out/sim_results.csv`; con `sweep`, la sensibilidad p × suelo en `_out/sim_sweep.csv` |
| `figures.py` | Figuras en `_out/figs/` |
| `_cache/Malbec_<inicio>_<fin>.json` | Clima y NDVI de cada una de las tres temporadas, descargados en junio de 2026. No se versionan (ver "Ubicación del sector") |
| `_out/` | Resultados de junio de 2026 |
| `sector_local.example.json` | Ubicación del sector con coordenadas redondeadas |

### Ejecución

Desde `backend/`:

```
venv/Scripts/python.exe evaluation/sim_efficiency.py
venv/Scripts/python.exe evaluation/sim_efficiency.py sweep
venv/Scripts/python.exe evaluation/figures.py
```

Los resultados de `_out/` se reproducen con el código del commit `64bf8b2`
(11/10/2026). Los dos scripts usan `app.calculation` (`figures.py`, a través de
`sim_efficiency.py`), que cambió después: desde `fcf6a9b` (12/10/2026: Kc sin
imagen reciente, inicio de la vid y humedad en la ETo) los resultados ya no
coinciden, y desde `d28c791` (21/10/2026) los scripts terminan con un
`TypeError`, porque `effective_precipitation` pasó a recibir también la ETo del
día.

Los scripts escriben en `_out/` y sobrescriben los resultados de junio. Para
compararlos, conviene correrlos sobre una copia de la carpeta dentro de `backend/`.
Los docstrings conservan las rutas originales (`scripts/`), de cuando los archivos
estaban en `backend/scripts/`. El comentario de la eficiencia en `sim_efficiency.py`
("aspersión (FAO-56: 85-90%)") también se conserva como estaba en junio, pero la
atribución es incorrecta: FAO-56 no da ese valor. La fuente del 0,85 para aspersión
es el DGI (Aquabook, "Uso del agua en agricultura. Sistemas de riego": 85–90 %) y
Schilardi et al. (2015, eficiencia potencial de 85 %).

### Ubicación del sector

El repositorio es público, por lo que la ubicación exacta del sector (coordenadas y
polígono) no se versiona: se lee de `sector_local.json`, ignorado por git. Si ese
archivo no existe, se usa `sector_local.example.json`, con las coordenadas
redondeadas a 0,1° (unos 10 km) y sin polígono.

Por la misma razón, tampoco se versionan el clima ni el NDVI descargados en el
sector (`_cache/Malbec_*`, ignorados por git). La simulación se reproduce a partir
de esos datos guardados localmente. Sin el polígono no se pueden volver a
descargar; si faltan, el script termina con un aviso.

Con las coordenadas redondeadas, el clima y el NDVI no cambian, porque vienen de
`_cache/`. Solo cambia la ETo, que depende de la latitud. Diferencia medida el
11/10/2026, con el código de `64bf8b2`:

- Con `sector_local.json`, `sim_results.csv` y `sim_sweep.csv` son idénticos a los
  de `_out/`.
- Con `sector_local.example.json`:
  - ETo estacional: entre −0,11 y −0,12 mm por temporada (−0,01 %); diferencia
    diaria máxima de 0,002 mm.
  - `sim_results.csv`: diferencias de hasta 0,1 (mm o días, según la columna; es la resolución del CSV).
  - `sim_sweep.csv`: el agua aplicada por el sistema cambia hasta 1,6 mm (0,43 %)
    y la percolación 0,6 mm en una fila. En `p=0.50/loam`, temporada 2021/22, el
    resultado sigue siendo "NO", pero lo supera un calendario en lugar de dos.
  - El resumen del barrido (Pareto-óptimo en las tres temporadas y rangos de
    ahorro) no cambia.

  Las diferencias se deben a que el sistema riega al cruzar RAW: una diferencia
  mínima de ETo puede mover un riego un día.

## Simulación final (octubre de 2026)

Simulación del protocolo de evaluación, la utilizada en la tesis. Desde `backend/`:

```
venv/Scripts/python.exe -m evaluation.final.run
venv/Scripts/python.exe -m evaluation.final.figures
```

Los resultados van a `final/_out/` y las figuras a `final/_out/figuras/`. Como la
simulación exploratoria, lee la latitud del sector de `sector_local.json` (ver
"Ubicación del sector") y usa datos del sector que no se versionan: el clima de
`_cache/open_meteo_2026-10-17/Malbec_clima_<inicio>_<fin>.json`, el NDVI de
`_cache/Malbec_<inicio>_<fin>.json` y la serie ERA5 de
`_cache/open_meteo_2026-10-17/Malbec_era5_1991-01-01_2024-04-30.json`. Los datos de
las estaciones (`_cache/*_diario_*.json` y
`_cache/open_meteo_2026-10-17/OpenMeteo_*.json`) sí se versionan.

### Lluvia frente a las estaciones

`final/climate_check.py` compara la lluvia de Open-Meteo (IFS y ERA5 en el sector)
con la de dos estaciones cercanas. La comparación se mantiene como diagnóstico
(`venv/Scripts/python.exe -m evaluation.final.climate_check`), pero no va a los
resultados de `final/_out/` ni se usa en la tesis, porque los datos de las
estaciones no permiten una comparación confiable:

- San Rafael Aero (SMN, OMM 87509; lluvia diaria del GSOD de NOAA): mezcla días
  armados con informes de 6 h (día UTC) con días de un único informe de 24 h que
  cierra a las 12 UTC. Además, cuatro informes de 24 h están contradichos por los
  de 6 h y por IFS y ERA5: 10/11/2020, 18/12/2020, 08/04/2021 y 11/01/2024.
- Rama Caída (INTA, estación A872933 del SIGA): la hora de cierre del día de lluvia
  no está documentada en el SIGA. En 2017/18 la estación registra 8,0 mm en 242
  días, frente a 241,9 mm de IFS y 304,9 mm de ERA5 (posible lluvia no registrada
  cargada como cero). En 2023/24 la columna cronológica suma 263,0 mm y la
  pluviométrica 67,0 mm; la diferencia, de 196,0 mm, se concentra en dos días: el
  10/02/2024 (113,5 mm en la cronológica y 0,25 mm en la pluviométrica) y el
  13/04/2024 (92,25 mm solo en la cronológica). En el resto de los días la
  pluviométrica suma 9,5 mm más.

La verificación de la ETo frente a las dos estaciones y la caracterización
climática con ERA5 se mantienen y van a `final/_out/`.
