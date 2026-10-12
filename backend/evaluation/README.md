# Evaluación: simulación de eficiencia hídrica

## Simulación exploratoria (junio de 2026)

Análisis exploratorio previo al protocolo de evaluación. Se versiona sin cambios
respecto de junio de 2026, salvo la ubicación del sector (ver "Ubicación del
sector"). No es la simulación utilizada en la tesis.

Compara, con el mismo balance hídrico FAO-56 del sistema (`app.calculation`), la
política del sistema (riega cuando el agotamiento alcanza RAW y repone a capacidad
de campo) contra calendarios fijos de 7, 10 y 14 días, dosificados al requerimiento
neto estacional o a la misma agua que aplicó el sistema. Usa clima ERA5 y NDVI
Sentinel-2 del sector Malbec en tres temporadas de riego (septiembre a abril,
2021/22 a 2023/24).

| Archivo | Contenido |
|---|---|
| `sim_efficiency.py` | Simulación. Sin argumentos genera `_out/sim_results.csv`; con `sweep`, la sensibilidad p × suelo en `_out/sim_sweep.csv` |
| `figures.py` | Figuras en `_out/figs/` |
| `_cache/` | Clima y NDVI de las tres temporadas, descargados en junio de 2026 |
| `_out/` | Resultados de junio de 2026 |
| `sector_local.example.json` | Ubicación del sector con coordenadas redondeadas |

### Ejecución

Desde `backend/`:

```
venv/Scripts/python.exe evaluation/sim_efficiency.py
venv/Scripts/python.exe evaluation/sim_efficiency.py sweep
venv/Scripts/python.exe evaluation/figures.py
```

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

La simulación se reproduce a partir de los datos guardados en `_cache/`. Sin el
polígono no se pueden volver a descargar; si falta `_cache/`, el script termina con
un aviso.

Con las coordenadas redondeadas, el clima y el NDVI no cambian, porque vienen de
`_cache/`. Solo cambia la ETo, que depende de la latitud. Diferencia medida el
11/10/2026:

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
