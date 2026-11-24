# Ecovertis — API / entrega final MIAD

Archivos **nuevos** que se copian a la raíz de `Ecovertis-miad`:

- `api_ecovertis.py` — API FastAPI, carga de cuatro modelos reales, validación y pronósticos recursivos.
- `requirements_api.txt` — dependencias reproducibles.
- `Dockerfile.api` — imagen para despliegue con Docker.
- `CONTRATO_API_PARA_KAREN.md` — contrato para que Karen integre Dash sin editar la API.

## Requisitos que deben existir previamente en el repo

- `modelos_entrega2.py` (sin modificar)
- `modelos_guardados/ingresos_ridge.joblib`
- `modelos_guardados/ingresos_random_forest.joblib`
- `modelos_guardados/opex_ajustado_ridge.joblib`
- `modelos_guardados/opex_ajustado_random_forest.joblib`
- `resultados/analisis_mensual_parques.csv`

## Probar en local

Usar Python 3.11 para aproximarse al contenedor. Desde la raíz del repositorio:

```bash
python3 -m venv .venv-api
source .venv-api/bin/activate
python -m pip install -r requirements_api.txt
python -m uvicorn api_ecovertis:app --host 127.0.0.1 --port 8001
```

Abre `http://127.0.0.1:8001/docs`, prueba `GET /health` y `POST /pronosticar`.

En otra terminal, ejecutar:

```bash
curl -X POST 'http://127.0.0.1:8001/pronosticar' \
  -H 'Content-Type: application/json' \
  -d '{"parque":"acacias","serie":"ingresos","modelo":"random_forest"}'
```

**Advertencia:** Si los `.joblib` fueron entrenados con otra versión de scikit-learn, deben comprobarse compatibilidades y, si hace falta, ajustar los pins del `requirements_api.txt` a la versión real del entrenamiento. No modificar los modelos sin evidencia.

## Docker

```bash
docker build -f Dockerfile.api -t ecovertis-api:final .
docker run --rm -p 8001:8001 ecovertis-api:final
```

`http://localhost:8001/docs` expone el contrato. El puerto local 8001 debe estar libre.

## Sobre los resultados

La validación original favoreció `ultimo_mes` frente a Ridge y Random Forest. La API incluye supervisados para cumplir la meta de inferencia, y referencias para comparaciones honestas. Los tres meses proyectados se calculan recursivamente. Son resultados exploratorios de datos simulados.

## Git: evidencia de autoría real

Hacer los commits **desde la cuenta de quien efectivamente modificó el código**. No inventar contribuciones. Evitar conflictos trabajando en ramas distintas. No incluir `.venv-api`, credenciales, claves AWS o datos sensibles en commits.
