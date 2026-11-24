"""API de pronósticos Ecovertis.

Usa los mismos modelos supervisados y exactamente la misma construcción
 de características de modelos_entrega2.py. No vuelve a entrenar.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal
import math

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from modelos_entrega2 import PARQUES, VARIABLES, cargar_datos, features

ROOT = Path(__file__).resolve().parent
MODELOS = ROOT / "modelos_guardados"
FUENTE = ROOT / "resultados" / "analisis_mensual_parques.csv"
SERIES = ("ingresos", "opex_ajustado")
SUPERVISADOS = ("ridge", "random_forest")
REFERENCIAS = ("ultimo_mes", "promedio_2_meses")
TODOS_MODELOS = SUPERVISADOS + REFERENCIAS
# cargar_datos() conserva los encabezados originales del CSV, no los nombres internos de la API.
ETIQUETAS_SERIE = {nombre_interno: encabezado_csv for encabezado_csv, nombre_interno in VARIABLES.items()}

Serie = Literal["ingresos", "opex_ajustado"]
Modelo = Literal["ridge", "random_forest", "ultimo_mes", "promedio_2_meses"]
Parque = Literal["acacias", "neiva", "puerto gaitan", "putumayo", "tanques"]

app = FastAPI(
    title="Ecovertis — API de pronósticos",
    description=("Predicciones exploratorias de ingresos y OPEX ajustado (COP), "
                 "basadas en modelos entrenados en la segunda entrega."),
    version="1.0.0",
)


class PrediccionEntrada(BaseModel):
    parque: Parque = Field(description="Parque en el formato utilizado para entrenar.")
    serie: Serie
    modelo: Modelo = "random_forest"
    mes: int = Field(ge=3, le=12, description="Número del mes (3 a 12).")
    lag1_cop: float = Field(ge=0, allow_inf_nan=False, description="Monto del mes anterior, en COP.")
    lag2_cop: float = Field(ge=0, allow_inf_nan=False, description="Monto de dos meses atrás, en COP.")


class PronosticoEntrada(BaseModel):
    parque: Parque
    serie: Serie
    modelo: Modelo = "random_forest"


@lru_cache(maxsize=4)
def cargar_modelo(serie: str, modelo: str):
    archivo = MODELOS / f"{serie}_{modelo}.joblib"
    if not archivo.is_file():
        raise HTTPException(status_code=503, detail=f"No se encontró el modelo: {archivo.name}")
    try:
        return joblib.load(archivo)
    except Exception as exc:
        # No exponer detalles de archivos o del servidor en la respuesta pública.
        raise HTTPException(
            status_code=503,
            detail="No se pudo cargar el modelo. Revisa las versiones de scikit-learn y joblib.",
        ) from exc


def inferir(parque: str, serie: str, modelo: str, mes: int, lag1: float, lag2: float) -> float:
    if modelo == "ultimo_mes":
        valor = lag1
    elif modelo == "promedio_2_meses":
        valor = (lag1 + lag2) / 2.0
    else:
        X = np.asarray([features(parque, mes, lag1, lag2)], dtype=float)
        estimador = cargar_modelo(serie, modelo)
        try:
            valor = float(estimador.predict(X)[0])
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Falló la inferencia del modelo.") from exc
    if not math.isfinite(valor):
        raise HTTPException(status_code=503, detail="El modelo devolvió un resultado no finito.")
    return max(0.0, float(valor))


@app.get("/")
def inicio():
    return {"servicio": "Ecovertis API", "version": app.version, "documentacion": "/docs"}


@app.get("/health")
def health():
    faltantes = [f"modelos_guardados/{s}_{m}.joblib"
                 for s in SERIES for m in SUPERVISADOS
                 if not (MODELOS / f"{s}_{m}.joblib").is_file()]
    if not FUENTE.is_file():
        faltantes.append("resultados/analisis_mensual_parques.csv")
    if faltantes:
        raise HTTPException(status_code=503, detail={"estado": "incompleto", "faltantes": faltantes})
    return {"estado": "ok", "modelos": len(SERIES) * len(SUPERVISADOS), "datos": "disponibles"}


@app.get("/catalogo")
def catalogo():
    return {
        "parques": list(PARQUES),
        "series": list(SERIES),
        "modelos_supervisados": list(SUPERVISADOS),
        "modelos_referencia": list(REFERENCIAS),
        "unidad_monetaria": "COP",
        "periodo_historico": "enero-septiembre de 2026",
        "alcance": "pronóstico a nivel de parque; no por proyecto",
    }


@app.post("/predecir")
def predecir(datos: PrediccionEntrada):
    pronostico = inferir(datos.parque, datos.serie, datos.modelo, datos.mes,
                        datos.lag1_cop, datos.lag2_cop)
    return {
        "parque": datos.parque,
        "serie": datos.serie,
        "modelo": datos.modelo,
        "tipo": "supervisado" if datos.modelo in SUPERVISADOS else "referencia",
        "mes": datos.mes,
        "prediccion_cop": round(pronostico, 2),
        "unidad": "COP",
        "advertencia": "Pronóstico experimental basado en nueve meses de historia.",
    }


@app.post("/pronosticar")
def pronosticar(datos: PronosticoEntrada):
    """Octubre a diciembre con actualización recursiva de los rezagos."""
    if not FUENTE.is_file():
        raise HTTPException(status_code=503, detail="Falta analisis_mensual_parques.csv")
    try:
        historico_original = cargar_datos()[datos.parque]
        historico = {m: historico_original[m][ETIQUETAS_SERIE[datos.serie]] for m in range(1, 10)}
    except (KeyError, ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=503, detail="Histórico mensual incompleto o inválido.") from exc

    filas = []
    for mes in (10, 11, 12):
        lag1, lag2 = historico[mes - 1], historico[mes - 2]
        valor = inferir(datos.parque, datos.serie, datos.modelo, mes, lag1, lag2)
        historico[mes] = valor
        filas.append({"mes": mes, "prediccion_cop": round(valor, 2)})

    return {
        "parque": datos.parque,
        "serie": datos.serie,
        "modelo": datos.modelo,
        "tipo": "supervisado" if datos.modelo in SUPERVISADOS else "referencia",
        "unidad": "COP",
        "pronosticos": filas,
        "metodologia": "recursiva; noviembre y diciembre usan pronósticos anteriores como rezagos",
        "advertencia": "Estimaciones exploratorias; no son presupuesto ni pronósticos por proyecto.",
    }
