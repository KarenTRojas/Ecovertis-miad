# Ecovertis — contrato de la API para integrar Dash

**Esta API no está desplegada todavía.** Primero Luis debe probarla con los cuatro `.joblib` del repositorio y el CSV mensual original. Cuando esté localmente encendida, Karen puede usar `http://127.0.0.1:8001`.

## Catálogo y comprobación

- `GET /health`: `{"estado":"ok", "modelos":4, "datos":"disponibles"}` si todos los archivos están presentes.
- `GET /catalogo`: parques, series, modelos y alcance.
- `GET /docs`: interfaz Swagger de FastAPI.

## Pronóstico octubre–diciembre por parque (recomendado para Dash)

`POST /pronosticar`

```json
{"parque":"acacias", "serie":"ingresos", "modelo":"random_forest"}
```

La respuesta devuelve un arreglo `pronosticos` con tres objetos `{ "mes": 10|11|12, "prediccion_cop": NUMERO }` y metadatos. Los valores NO deben asumirse hasta ejecutar la API real.

Valores permitidos:

- `parque`: `acacias`, `neiva`, `puerto gaitan`, `putumayo`, `tanques`.
- `serie`: `ingresos`, `opex_ajustado`.
- `modelo`: `ridge`, `random_forest`, `ultimo_mes`, `promedio_2_meses`.

## Predicción para una sola combinación de rezagos

`POST /predecir`

```json
{"parque":"acacias", "serie":"ingresos", "modelo":"ridge", "mes":10, "lag1_cop":500000000, "lag2_cop":480000000}
```

Los montos de ejemplo son exclusivamente para comprobar el formato; **no son valores observados de Ecovertis**.

## Reglas de integración

1. Los pronósticos son por **parque**, nunca por proyecto. Cuando se seleccione un proyecto, mostrar solo el histórico o advertir que no existe proyección desagregada.
2. No cambiar la representación interna de parques o variables sin coordinarla con la API.
3. Distinguir visualmente observados y proyectados.
4. Dejar elegir modelo para comparar Ridge/Random Forest con las referencias, pero **no afirmar que un supervisado supera el último mes**: en la segunda entrega fue al revés.
5. No entrenar modelos desde Dash; toda inferencia debe viajar a la API.
6. Karen hará commits de `tablero_ecovertis.py`, `assets/ecovertis.css`, `MANUAL_USUARIO.md` o pruebas que ella efectivamente realice. No incluir en sus commits archivos de API de Luis.
7. El host de API será configurable para Docker o nube: `ECO_API_URL`.

## Ejemplo mínimo de consumo desde Dash

```python
import os
import requests

API_BASE = os.environ.get("ECO_API_URL", "http://127.0.0.1:8001")
respuesta = requests.post(
    f"{API_BASE}/pronosticar",
    json={"parque": "acacias", "serie": "ingresos", "modelo": "random_forest"},
    timeout=20,
)
respuesta.raise_for_status()
filas = respuesta.json()["pronosticos"]
```

Este ejemplo no modifica el tablero existente. La adaptación debe revisarse contra sus callbacks reales.
