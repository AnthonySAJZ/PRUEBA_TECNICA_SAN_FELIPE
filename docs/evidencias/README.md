# Evidencias de ejecución de los scripts SQL

Salidas de `sqlcmd` al ejecutar los scripts de `sql/` en orden, sobre **SQL Server 2022 (16.x) en Docker/Linux**:

| Archivo | Script |
|---|---|
| `salida_01_creacion.txt` | `01_creacion_tablas.sql` |
| `salida_02_ingesta.txt` | `02_ingesta_bulk_insert.sql` (7,158 filas leídas y cargadas) |
| `salida_03_perfilado.txt` | `03_perfilado.sql` (todas las consultas de perfilado) |
| `salida_04_carga_limpios.txt` | `04_carga_datos_limpios.sql` (comparación Antes vs Después) |

Diferencias respecto a una instalación en Windows (ya documentadas dentro de cada script):
- Rutas: `/data/...` en lugar de `C:\PruebaSanFelipe\...`.
- `02`: `@CodePage = 'RAW'` (Linux no admite `CODEPAGE = '1252'`).
- `04`: archivo en UTF-16 con `DATAFILETYPE = 'widechar'` (Linux no admite `CODEPAGE = '65001'`).
