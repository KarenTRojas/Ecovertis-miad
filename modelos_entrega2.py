"""Ecovertis — comparación de modelos y pronóstico octubre–diciembre 2026.

Entrenamiento con datos mensuales por parque calculados en Exploracion.py.
Validación de meses 8 y 9 (pronósticos de un paso con información disponible hasta el mes anterior).
No utiliza datos futuros para construir características.
"""
from __future__ import annotations
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import joblib
import numpy as np
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent
RESULTADOS = ROOT / "resultados"
MODELOS = ROOT / "modelos_guardados"
RESULTADOS.mkdir(exist_ok=True)
MODELOS.mkdir(exist_ok=True)
FUENTE = RESULTADOS / "analisis_mensual_parques.csv"
PARQUES = ("acacias", "neiva", "puerto gaitan", "putumayo", "tanques")
VARIABLES = {"Ingresos": "ingresos", "OPEX ajustado": "opex_ajustado"}
MESES = {10:"Octubre",11:"Noviembre",12:"Diciembre"}


def cargar_datos():
    if not FUENTE.exists():
        raise FileNotFoundError(f"Falta {FUENTE}. Ejecuta Exploracion.py del repositorio de Ecovertis.")
    d = defaultdict(dict)
    with open(FUENTE, encoding="utf-8-sig", newline="") as archivo:
        for item in csv.DictReader(archivo):
            mes = int(item["Periodo"].split(".")[0])
            p = item["Parque"].strip().lower()
            if p in PARQUES:
                d[p][mes] = {v:float(item[v]) for v in VARIABLES}
    for p in PARQUES:
        if set(d[p]) != set(range(1,10)):
            raise ValueError(f"Faltan meses enero–septiembre en el parque {p}: {sorted(d[p])}")
    return d


def features(parque, mes, lag1, lag2):
    # Escala logarítmica de ingresos y costos, con parque codificado mediante indicadores.
    return [float(mes), math.log1p(max(0.0,lag1)), math.log1p(max(0.0,lag2))] + [float(parque == p) for p in PARQUES]


def preparar(d, variable, meses):
    X, y, etiquetas = [], [], []
    for parque in PARQUES:
        for mes in meses:
            serie=d[parque]
            X.append(features(parque,mes,serie[mes-1][variable],serie[mes-2][variable]))
            y.append(serie[mes][variable])
            etiquetas.append((parque,mes))
    return np.array(X,dtype=float),np.array(y,dtype=float),etiquetas


def crear_estimador(nombre):
    if nombre == "ridge":
        regresor=make_pipeline(StandardScaler(), Ridge(alpha=6.0))
        return TransformedTargetRegressor(regressor=regresor,func=np.log1p,inverse_func=np.expm1,check_inverse=False)
    if nombre == "random_forest":
        regresor=RandomForestRegressor(n_estimators=160,max_depth=5,min_samples_leaf=2,random_state=42,n_jobs=-1)
        return TransformedTargetRegressor(regressor=regresor,func=np.log1p,inverse_func=np.expm1,check_inverse=False)
    raise ValueError(nombre)


def predecir(nombre, X, modelo=None):
    if nombre == "ultimo_mes":
        return np.expm1(X[:,1])
    if nombre == "promedio_2_meses":
        return (np.expm1(X[:,1]) + np.expm1(X[:,2])) / 2.0
    return np.maximum(0.0,modelo.predict(X))


def metricas(y, pred):
    y = np.asarray(y,float);pred=np.asarray(pred,float)
    error=np.abs(y-pred)
    return {
        "mae_cop": float(np.mean(error)),
        "rmse_cop":float(np.sqrt(np.mean((y-pred)**2))),
        "wape_pct":float(100*sum(error)/sum(np.abs(y))) if sum(np.abs(y)) else None,
        "observaciones":len(y),
    }


def escribir_csv(ruta, filas, columnas):
    with open(ruta,"w",encoding="utf-8-sig",newline="") as archivo:
        escritor=csv.DictWriter(archivo,fieldnames=columnas)
        escritor.writeheader();escritor.writerows(filas)


def registrar_en_mlflow(nombre, etiquetas, params, medidas, modelo=None):
    try:
        import mlflow
    except ImportError:
        return False
    mlflow.set_experiment("ecovertis_entrega2_2026")
    with mlflow.start_run(run_name=nombre):
        mlflow.set_tags({"proyecto":"Ecovertis", "validacion":"holdout_agosto_septiembre_2026", "dataset":"enero_septiembre_2026"})
        mlflow.log_params({**params, "serie":etiquetas})
        mlflow.log_metrics({k:v for k,v in medidas.items() if v is not None})
        if modelo is not None:
            import mlflow.sklearn
            mlflow.sklearn.log_model(modelo, artifact_path="modelo")
    return True


def ejecutar():
    datos=cargar_datos()
    comparaciones=[];validaciones=[];pronosticos=[];log_activo=False
    for variable,ident in VARIABLES.items():
        # Entrenar solo con marzo–julio. Evaluar agosto y septiembre sin entrenar sobre esos meses.
        x_train,y_train,_ = preparar(datos,variable,range(3,8))
        x_test,y_test,labels = preparar(datos,variable,[8,9])
        seleccionados={}
        for nombre in ("ultimo_mes","promedio_2_meses","ridge","random_forest"):
            model=None
            if nombre in ("ridge","random_forest"):
                model=crear_estimador(nombre)
                model.fit(x_train,np.maximum(0,y_train))
            estimaciones=predecir(nombre,x_test,model)
            m=metricas(y_test,estimaciones)
            comparaciones.append({"serie":ident,"modelo":nombre,"mae_millones_cop":round(m["mae_cop"]/1e6,3),"rmse_millones_cop":round(m["rmse_cop"]/1e6,3),"wape_pct":round(m["wape_pct"],2),"n_validacion":m["observaciones"]})
            seleccionados[nombre]=m
            log_activo=registrar_en_mlflow(f"{ident}_{nombre}",ident,{"algoritmo":nombre,"train_meses":"03-07", "test_meses":"08-09","n_train":len(y_train)},m,modelo=model) or log_activo
            for idx,(parque,mes) in enumerate(labels):
                validaciones.append({"serie":ident,"modelo":nombre,"parque":parque,"mes":mes,"observado_cop":round(float(y_test[idx]),2),"predicho_cop":round(float(estimaciones[idx]),2)})
        ganador=min(seleccionados,key=lambda nom:seleccionados[nom]["wape_pct"])
        # Se muestra qué alternativa ganó, aunque sea un pronóstico ingenuo.
        # Reentrenar ML sobre todos los meses disponibles antes de pronosticar octubre–diciembre.
        modelo_final=None
        if ganador in ("ridge","random_forest"):
            x_total,y_total,_=preparar(datos,variable,range(3,10))
            modelo_final=crear_estimador(ganador)
            modelo_final.fit(x_total,np.maximum(0,y_total))
            joblib.dump(modelo_final,MODELOS/f"{ident}_{ganador}.joblib")
        # Guardar también ambos supervisados (independientemente del ganador), para comparación futura.
        for nombre in ("ridge","random_forest"):
            if nombre != ganador:
                x_total,y_total,_=preparar(datos,variable,range(3,10))
                m2=crear_estimador(nombre)
                m2.fit(x_total,np.maximum(0,y_total))
                joblib.dump(m2,MODELOS/f"{ident}_{nombre}.joblib")
        for parque in PARQUES:
            historico={m:datos[parque][m][variable] for m in range(1,10)}
            for mes in range(10,13):
                x=np.asarray([features(parque,mes,historico[mes-1],historico[mes-2])],dtype=float)
                pron=float(predecir(ganador,x,modelo_final)[0])
                historico[mes]=pron
                pronosticos.append({"periodo":f"{mes:02d}. {MESES[mes]}","mes":mes,"parque":parque,"variable":ident,"pronostico_cop":round(pron,2),"modelo_seleccionado":ganador})
    escribir_csv(RESULTADOS/"comparacion_modelos.csv",comparaciones,["serie","modelo","mae_millones_cop","rmse_millones_cop","wape_pct","n_validacion"])
    escribir_csv(RESULTADOS/"validacion_agosto_septiembre.csv",validaciones,["serie","modelo","parque","mes","observado_cop","predicho_cop"])
    escribir_csv(RESULTADOS/"pronostico_oct_dic_2026.csv",pronosticos,["periodo","mes","parque","variable","pronostico_cop","modelo_seleccionado"])
    print("\nCOMPARACIÓN DE MODELOS (agosto–septiembre 2026)")
    for r in comparaciones: print(f"{r['serie']:16s} {r['modelo']:18s} MAE={r['mae_millones_cop']:10.2f} M COP  WAPE={r['wape_pct']:6.2f}%")
    print("\nModelos supervisados y archivos CSV guardados en",ROOT)
    print("Experimentos MLflow:","registrados" if log_activo else "NO registrados: instala mlflow y vuelve a ejecutar")
    print("AVISO: son predicciones experimentales con solo 9 meses de historia.")

if __name__=='__main__': ejecutar()
