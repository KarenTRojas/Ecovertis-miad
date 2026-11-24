# Ecovertis · Encargo para Karen — Entrega final
**Proyecto:** MIAD, Despliegue de Soluciones Analíticas  
**Fecha:** 24 de noviembre de 2026  
**Objetivo:** Integrar Dash con una API de predicción ya desarrollada, conservando los filtros y aportando commits propios.

## Dependencia inicial de Git
Repositorio: https://github.com/KarenTRojas/Ecovertis-miad

**Antes de crear la rama de Karen:** confirmar que el PR `feature/api-docker-luis` → `master` se haya integrado. Si no, coordinar ese merge primero. No trabajar sobre una copia antigua de `master`.

```bash
git switch master
git pull --ff-only origin master
git switch -c feature/dash-api-karen
```

## Alcance de Karen
1. Modificar `tablero_ecovertis.py` para que las predicciones de ingresos/OPEX se soliciten a FastAPI, en vez de depender exclusivamente de CSV precalculados.
2. Mantener las visualizaciones históricas y filtros existentes, y distinguir observado versus pronosticado.
3. Añadir al tablero controles de parque, serie (`ingresos` / `opex_ajustado`) y modelo (`ridge`, `random_forest`, `ultimo_mes`, `promedio_2_meses`) donde aporten valor al usuario. No mostrar predicciones por proyecto: el modelo se entrenó por parque.
4. Manejar errores de conexión de la API con un mensaje visible y entendible, sin romper todo el tablero.
5. Escribir `MANUAL_USUARIO_ECOVERTIS.md` (opciones del tablero, pasos, interpretación, alcance y limitaciones).
6. Ejecutar las pruebas locales, capturar evidencias y realizar commits desde su identidad de GitHub.

## Contrato técnico real
Variable de entorno: `ECO_API_URL`
- Desarrollo, si **ella ejecuta FastAPI en su computadora**: `http://127.0.0.1:8001`
- Contenedores en la misma red Docker Compose (configuración objetivo): `http://api:8001`
- AWS EC2: usar dirección pública solo para pruebas externas, no dejarla escrita en el código; puede cambiar cuando la instancia se detiene.

Endpoints:
- `GET /health`: diagnóstico
- `GET /catalogo`: opciones autorizadas
- `POST /pronosticar` (recomendado para tablero)
- `POST /predecir`: inferencia de un mes con lag1 y lag2

Solicitud a `/pronosticar`:
```json
{"parque":"acacias","serie":"ingresos","modelo":"random_forest"}
```

Respuesta: JSON con `parque`, `serie`, `modelo`, `tipo`, `unidad` y la lista
`pronosticos` de tres objetos `{ "mes": 10/11/12, "prediccion_cop": monto }`.

Ejemplo de uso dentro de un callback Dash:
```python
import os
import requests

def consultar_pronostico(parque: str, serie: str, modelo: str):
    base = os.getenv("ECO_API_URL", "http://127.0.0.1:8001").rstrip("/")
    r = requests.post(
        f"{base}/pronosticar",
        json={"parque": parque, "serie": serie, "modelo": modelo},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()["pronosticos"]
```
En cualquier gráfico que se mida en **millones de COP**, convertir `prediccion_cop / 1_000_000` y rotular la unidad. No confundir COP con millones.

## Pruebas y evidencia que debe entregar Karen
- Captura del tablero consumiendo una predicción real de FastAPI; para eso puede levantar la API localmente (no requiere EC2).
- Comprobación de ingresos y OPEX, como mínimo en dos parques.
- Comportamiento al apagar FastAPI: mensaje de error controlado.
- Pantallazo de `git log` donde figuren sus commits y vínculo a su PR.
- Manual de usuario completo con capturas correspondientes a la versión final del tablero.

## Versionado y trabajo en equipo
Archivos prioritarios de Karen: `tablero_ecovertis.py`, `assets/ecovertis.css`, `MANUAL_USUARIO_ECOVERTIS.md` y pruebas relacionadas. Evitar editar `api_ecovertis.py`, `Dockerfile.api` o los `.joblib` sin coordinación.

```bash
git status --short
git add tablero_ecovertis.py assets/ecovertis.css MANUAL_USUARIO_ECOVERTIS.md
git commit -m "Entrega final: conectar tablero Dash con API de Ecovertis"
git push -u origin feature/dash-api-karen
```
Ajustar `git add` a los archivos realmente modificados. Hacer más de un commit si hay avances separados verificables.

## Cuándo avisarle a Luis para encender EC2
**No se necesita AWS para desarrollar ni probar localmente la integración.** Pedir encender EC2 una vez que:
1. El tablero consume `/pronosticar` localmente sin errores.
2. La rama y los commits están publicados.
3. Hay una versión razonablemente estable para la prueba de integración de ambos contenedores, las capturas y el video.

Hasta entonces, desarrollar en local. Si no puede ejecutar la API, coordinar una sesión breve de pruebas externas una vez que el tablero esté preparado.

## Video
Karen: contexto del problema, navegación del tablero, consulta en vivo y resultados; duración orientativa de 4–5 minutos. Luis: modelos, API, despliegue Docker/AWS y conclusión, 4–5 minutos. Deben participar ambos, mostrando recursos reales y resultados demostrados. Duración total máxima: 10 minutos.
