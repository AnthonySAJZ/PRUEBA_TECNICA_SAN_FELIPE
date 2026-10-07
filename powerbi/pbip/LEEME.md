# Proyecto Power BI (PBIP)

Abrir `Dashboard_Requerimientos.pbip` con Power BI Desktop (agosto 2025 o posterior).

1. El reporte abre **sin datos** (el proyecto no versiona `cache.abf`).
2. Inicio > Transformar datos (flecha) > **Editar parámetros** > `RutaArchivoCSV` = ruta
   absoluta de `data\clean\RequerimientosPruebaDatos_Limpio.csv` en tu equipo > Aceptar > Aplicar cambios.
3. Inicio > **Actualizar**.
4. Comprobar los valores de control: Q Tickets 3,406 · Q Horas 16,979 · Promedio Horas x Ticket 4.98 · % Resueltos 98.4%.

Detalle, requisitos y solución de problemas: `../GUIA_POWER_BI.md`.
Este proyecto lo genera `python/generar_pbip.py`; no editar a mano lo que se vaya a regenerar.
