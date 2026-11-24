# Ecovertis · carpeta de la entrega final

**Corte documentado:** 24 de noviembre de 2026. **Estado:** borradores y evidencias de avance; no representan la entrega final cerrada.

## Archivos

| Archivo | Uso | Estado |
|---|---|---|
| `Informe_Avance_Ecovertis_Entrega_Final.docx` | Informe editable, continuar con evidencias de Karen | Avance 8 páginas |
| `Informe_Avance_Ecovertis_Entrega_Final.pdf` | Vista de lectura del informe al corte | Avance |
| `Presentacion_Ecovertis_Avance_Final.pptx` | Presentación editable; reutiliza estilo de presentación MIAD | Avance |
| `Presentacion_Ecovertis_Avance_Final.pdf` | Vista de las diapositivas | Avance |
| `Manual_Instalacion_Ecovertis_Borrador.md` | Operación de la API en Docker y EC2 | Falta completar Dash |
| `Encargo_Karen_Entrega_Final.md` | Actividades, contrato y criterios de aceptación para Karen | Guía de trabajo |
| `README_Entrega_Final.md` | Índice, control de versiones y cierre | Actualizable |

**El guion de video se comparte por separado y no está en esta carpeta.**

## Para continuar

1. Comprobar si el PR de `feature/api-docker-luis` se integró a `master`; no asumir el merge por el solo `git push`.
2. Karen trabaja en su rama `feature/dash-api-karen`: integra `/pronosticar`, maneja errores, verifica resultados y realiza commits propios.
3. Luis completa el despliegue del tablero y prueba ambos servicios en EC2, y actualiza el manual de instalación.
4. Sustituir en el informe las partes pendientes solo después de obtener evidencia real: Dash conectado, pruebas de ingreso/OPEX, video y trabajo en equipo.
5. Preparar captura de `git log` y vínculos a PR, además de la URL vigente de AWS (que puede cambiar al reiniciar EC2).

## Precauciones

- No subir llaves `.pem`, credenciales AWS ni archivos privados a Git.
- La API se probó por HTTP; no presentarla como servicio de producción seguro.
- Los modelos usan datos simulados y la validación solo cubre agosto y septiembre de 2026.
- El reporte final del curso tiene límite de diez páginas; esta versión tiene ocho.
- La instancia debe detenerse (no terminarse) después de la captura de evidencias.
