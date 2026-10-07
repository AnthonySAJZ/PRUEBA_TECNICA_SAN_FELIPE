# Borrador del correo de envío

> Completar los datos entre corchetes y enviarlo desde el correo personal. Las instrucciones de la prueba piden incluir el identificador en el **cuerpo** del correo.

## Antes de enviar

- [ ] Fusionar el PR en `main` (hoy `main` solo tiene el README inicial) y comprobar en una ventana de incógnito que el repositorio muestra todas las carpetas.
- [ ] Decidir la visibilidad del repositorio: público, o privado y adjuntar un ZIP de `main` (el repo contiene los usuarios internos del archivo de la prueba).
- [ ] En Power BI Desktop para Windows: abrir `powerbi/pbip/Dashboard_Requerimientos.pbip`, ajustar `RutaArchivoCSV`, *Actualizar*, comprobar 3,406 · 16,979 · 4.98 · 98.4% y *Guardar como* `powerbi/Dashboard_Requerimientos.pbix`. Versionarlo o adjuntarlo y anotar la versión de Desktop (*Ayuda > Acerca de*). No guardar los cambios del `.pbip` (o descartarlos con `git checkout -- powerbi/pbip`).
- [ ] Regenerar el informe con el nombre: `python python/generar_informe.py --autor "Apellidos y Nombres"`.
- [ ] Grabar el video con `docs/GUION_VIDEO.md`, subirlo (YouTube no listado, Drive o Loom) y poner el enlace en el README (fila 6) y abajo.
- [ ] Si las reglas de la evaluación lo piden, declarar las herramientas de asistencia usadas.

**Para:** hvidal@clinicasanfelipe.com
**Asunto:** Prueba Técnica Analista de Datos – [Apellidos y Nombres completos]

---

Estimado(a):

Analista de Datos + [Número de Documento] + [Apellidos y Nombres completos]

Adjunto la resolución de la prueba técnica de Analista de Datos. El detalle completo está en el repositorio: [enlace al repositorio de GitHub].

Entregables:
1. Archivo de datos limpios: `RequerimientosPruebaDatos_Limpio.csv` (y versión `.xlsx` con diccionario y bitácora de limpieza).
2. Scripts SQL de carga e inspección: `01_creacion_tablas.sql`, `02_ingesta_bulk_insert.sql`, `03_perfilado.sql`, `04_carga_datos_limpios.sql`.
3. Script de limpieza `limpieza.py` y cuaderno `EDA_Requerimientos.ipynb`.
4. Archivo Power BI `Dashboard_Requerimientos.pbix` (abre con los datos incluidos) y su proyecto fuente `Dashboard_Requerimientos.pbip`, el dashboard interactivo `Dashboard_Requerimientos.html` y las medidas DAX.
5. Informe ejecutivo `Informe_Ejecutivo.pdf`.
6. Video explicativo: [enlace al video].

Quedo atento(a) a cualquier consulta.

Saludos cordiales,
[Apellidos y Nombres]
[Teléfono]
