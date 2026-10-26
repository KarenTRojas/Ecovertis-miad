from pathlib import Path
import pandas as pd
pd.set_option("display.float_format", "{:,.2f}".format)

# =====================================================
# 1. CONFIGURACIÓN
# =====================================================

# Carpeta donde está guardado el archivo .py
BASE = Path(__file__).resolve().parent

# Excel ubicado en la misma carpeta del .py
ARCHIVO = BASE / "2026 Base de Datos Ejecucion.xlsx"

# Carpeta para guardar resultados
SALIDA = BASE / "resultados"
SALIDA.mkdir(exist_ok=True)

HOJAS = ["EJECUCION Ingresos", "EJECUCION Costos"]


# =====================================================
# 2. DESCRIPCIÓN DE LOS CONJUNTOS
# =====================================================

def describir_datos(nombre_hoja):
    print(f"\n{'=' * 65}")
    print(f"CONJUNTO DE DATOS: {nombre_hoja}")
    print("=" * 65)

    df = pd.read_excel(ARCHIVO, sheet_name=nombre_hoja)

    # Eliminar columnas completamente vacías
    df = df.dropna(axis=1, how="all")

    print(f"\nNúmero de registros: {len(df):,}")
    print(f"Número de columnas: {len(df.columns)}")

    # Descripción de las variables
    descripcion = pd.DataFrame({
        "Variable": df.columns,
        "Tipo de dato": df.dtypes.astype(str).values,
        "Valores no nulos": df.notna().sum().values,
        "Valores faltantes": df.isna().sum().values,
        "% faltantes": (df.isna().mean() * 100).round(2).values,
        "Valores únicos": df.nunique(dropna=True).values
    })

    print("\n--- DESCRIPCIÓN DE VARIABLES ---")
    print(descripcion.to_string(index=False))

    # Calidad inicial
    print("\n--- CALIDAD DE DATOS ---")
    print(f"Filas duplicadas exactas: {df.duplicated().sum()}")
    print(f"Filas con algún valor faltante: {df.isna().any(axis=1).sum()}")

    # Estadísticas de variables numéricas
    numericas = df.select_dtypes(include="number")

    if not numericas.empty:
        print("\n--- ESTADÍSTICAS NUMÉRICAS ---")
        print(numericas.describe().round(2).to_string())

    # Guardar únicamente resultados descriptivos
    nombre = "ingresos" if "Ingresos" in nombre_hoja else "costos"
    descripcion.to_csv(
        SALIDA / f"descripcion_{nombre}.csv",
        index=False,
        encoding="utf-8-sig"
    )

    return df


# =====================================================
# 3. EJECUCIÓN
# =====================================================

if __name__ == "__main__":
    if not ARCHIVO.exists():
        raise FileNotFoundError(f"No se encontró el Excel: {ARCHIVO}")

    libro = pd.ExcelFile(ARCHIVO)
    print("Hojas disponibles:", libro.sheet_names)

    for hoja in HOJAS:
        if hoja not in libro.sheet_names:
            print(f"\nADVERTENCIA: No existe la hoja '{hoja}'")
            continue

        describir_datos(hoja)

    print("\nDescripción finalizada.")
    print(f"Resultados guardados en: {SALIDA}")

# =====================================================
# 4. VALIDACIÓN DE ESTRUCTURA Y CONSISTENCIA
# =====================================================

ingresos = pd.read_excel(ARCHIVO, sheet_name="EJECUCION Ingresos")
costos = pd.read_excel(ARCHIVO, sheet_name="EJECUCION Costos")

print("\n--- PARQUES EN INGRESOS ---")
print(ingresos["PARQUE ECOLOGICO"].value_counts().to_string())

print("\n--- PLANTAS EN COSTOS ---")
print(costos["Planta"].value_counts().to_string())

print("\n--- MESES EN INGRESOS ---")
print(ingresos["MES"].value_counts().sort_index().to_string())

print("\n--- MESES EN COSTOS ---")
print(costos["Mes"].value_counts().sort_index().to_string())

print("\n--- COMPARACIÓN VALOR Y COSTO ---")
coinciden = costos["Valor"].equals(costos["Costo"])
print("¿Las columnas son idénticas?:", coinciden)

print("\n--- PROYECTOS EN INGRESOS ---")
print(ingresos["PROYECTO"].value_counts().to_string())

print("\n--- PROYECTOS EN COSTOS ---")
print(costos["Proyecto"].value_counts().to_string())

# =====================================================
# 5. ANÁLISIS EXPLORATORIO MENSUAL
# =====================================================

import matplotlib.pyplot as plt

# Orden cronológico de los meses
meses = [
    "01. Enero", "02. Febrero", "03. Marzo",
    "04. Abril", "05. Mayo", "06. Junio",
    "07. Julio", "08. Agosto", "09. Septiembre"
]

# Consolidar ingresos y costos por mes
ingresos_mes = ingresos.groupby("MES")["INGRESO TOTAL"].sum()
costos_mes = costos.groupby("Mes")["Costo"].sum()

# Crear tabla consolidada
resumen = pd.DataFrame({
    "Ingresos": ingresos_mes,
    "OPEX": costos_mes
}).reindex(meses).fillna(0)

# Calcular indicadores
resumen["Resultado estimado"] = (
    resumen["Ingresos"] - resumen["OPEX"]
)

resumen["Margen estimado (%)"] = (
    resumen["Resultado estimado"]
    .div(resumen["Ingresos"].replace(0, float("nan")))
    * 100
)

# Formato de presentación de la tabla financiera
formato = {
    "Ingresos": "{:,.0f}".format,
    "OPEX": "{:,.0f}".format,
    "Resultado estimado": "{:,.0f}".format,
    "Margen estimado (%)": "{:.2f}".format
}

print("\n--- RESUMEN FINANCIERO MENSUAL ---")
print(resumen.to_string(formatters=formato))

# Guardar tabla
resumen.to_csv(
    SALIDA / "resumen_financiero_mensual.csv",
    encoding="utf-8-sig"
)

# =====================================================
# 6. GRÁFICA COMBINADA: INGRESOS, OPEX Y MARGEN
# =====================================================

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

fig, ax1 = plt.subplots(figsize=(12, 6))

# Eje principal: ingresos y costos en millones de COP
linea1, = ax1.plot(
    meses,
    resumen["Ingresos"] / 1_000_000,
    marker="o",
    linewidth=2,
    label="Ingresos"
)

linea2, = ax1.plot(
    meses,
    resumen["OPEX"] / 1_000_000,
    marker="o",
    linewidth=2,
    label="OPEX"
)

ax1.set_xlabel("Mes")
ax1.set_ylabel("Millones de COP")
ax1.tick_params(axis="x", rotation=40)
ax1.grid(alpha=0.25)

# Eje secundario: margen operativo estimado
ax2 = ax1.twinx()

linea3, = ax2.plot(
    meses,
    resumen["Margen estimado (%)"],
    marker="s",
    linestyle="--",
    linewidth=2,
    color="green",
    label="Margen operativo estimado"
)

ax2.set_ylabel("Margen operativo estimado (%)")
ax2.yaxis.set_major_formatter(
    FuncFormatter(lambda valor, pos: f"{valor:.0f}%")
)

# Leyenda conjunta
lineas = [linea1, linea2, linea3]
etiquetas = [linea.get_label() for linea in lineas]

ax1.legend(
    lineas,
    etiquetas,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.23),
    ncol=3
)

plt.title(
    "Evolución de ingresos, OPEX y margen operativo estimado - 2026"
)

plt.tight_layout()

# Guardar figura para el informe
plt.savefig(
    SALIDA / "evolucion_financiera_combinada.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

# =====================================================
# 8. ANÁLISIS FINANCIERO POR PARQUE ECOLÓGICO
# =====================================================

# Homologar nombres de ubicación
ingresos["Parque"] = ingresos["PARQUE ECOLOGICO"].str.strip().str.casefold()
costos["Parque"] = costos["Planta"].str.strip().str.casefold()

# Homologar nombres de meses
ingresos["Periodo"] = ingresos["MES"].str.strip()
costos["Periodo"] = costos["Mes"].str.strip()

# Parques identificados en ingresos
parques = sorted(ingresos["Parque"].unique())

# Separar costos compartidos y directos
costos_compartidos = costos[costos["Parque"] == "operaciones"].copy()
costos_directos = costos[costos["Parque"] != "operaciones"].copy()

# Validar ubicaciones en costos
ubicaciones_sin_correspondencia = set(
    costos_directos["Parque"].unique()
) - set(parques)

if ubicaciones_sin_correspondencia:
    raise ValueError(
        "Existen plantas sin correspondencia en ingresos: "
        f"{ubicaciones_sin_correspondencia}"
    )

# Consolidar ingresos por parque y mes
ingresos_parque = (
    ingresos.groupby(["Periodo", "Parque"])["INGRESO TOTAL"]
    .sum()
    .rename("Ingresos")
    .reset_index()
)

# Consolidar OPEX directo por parque y mes
opex_directo = (
    costos_directos.groupby(["Periodo", "Parque"])["Costo"]
    .sum()
    .rename("OPEX directo")
    .reset_index()
)

# Consolidar OPEX compartido de Operaciones por mes
opex_compartido = (
    costos_compartidos.groupby("Periodo")["Costo"]
    .sum()
    .rename("OPEX compartido total")
    .reset_index()
)

# Combinar información
analisis_parques = pd.merge(
    ingresos_parque,
    opex_directo,
    on=["Periodo", "Parque"],
    how="outer"
)

analisis_parques = pd.merge(
    analisis_parques,
    opex_compartido,
    on="Periodo",
    how="left"
)

analisis_parques[
    ["Ingresos", "OPEX directo", "OPEX compartido total"]
] = analisis_parques[
    ["Ingresos", "OPEX directo", "OPEX compartido total"]
].fillna(0)

# Participación de cada parque en los ingresos mensuales
total_ingresos_mes = analisis_parques.groupby(
    "Periodo"
)["Ingresos"].transform("sum")

if (total_ingresos_mes <= 0).any():
    raise ValueError(
        "Hay meses con ingresos consolidados no positivos. "
        "Revisar el criterio de prorrateo."
    )

analisis_parques["Participacion"] = (
    analisis_parques["Ingresos"] / total_ingresos_mes
)

# Asignación de costos compartidos
analisis_parques["OPEX asignado"] = (
    analisis_parques["OPEX compartido total"]
    * analisis_parques["Participacion"]
)

# Cálculos financieros
analisis_parques["OPEX ajustado"] = (
    analisis_parques["OPEX directo"]
    + analisis_parques["OPEX asignado"]
)

analisis_parques["Resultado estimado"] = (
    analisis_parques["Ingresos"]
    - analisis_parques["OPEX ajustado"]
)

# Consolidado enero-septiembre por parque
resumen_parques = analisis_parques.groupby("Parque")[
    ["Ingresos", "OPEX directo", "OPEX asignado",
     "OPEX ajustado", "Resultado estimado"]
].sum()

resumen_parques["Margen estimado (%)"] = (
    resumen_parques["Resultado estimado"]
    / resumen_parques["Ingresos"].replace(0, float("nan"))
    * 100
)

# Mostrar tabla
formato_parques = {
    columna: "{:,.0f}".format
    for columna in [
        "Ingresos", "OPEX directo", "OPEX asignado",
        "OPEX ajustado", "Resultado estimado"
    ]
}
formato_parques["Margen estimado (%)"] = "{:.2f}".format

print("\n--- RESUMEN FINANCIERO POR PARQUE ---")
print(resumen_parques.to_string(formatters=formato_parques))

# Verificar conciliación de OPEX
opex_original = costos["Costo"].sum()
opex_distribuido = resumen_parques["OPEX ajustado"].sum()

print("\n--- CONCILIACIÓN DE COSTOS ---")
print(f"OPEX original:    {opex_original:,.0f}")
print(f"OPEX distribuido: {opex_distribuido:,.0f}")
print(f"Diferencia:       {opex_original - opex_distribuido:,.2f}")

if abs(opex_original - opex_distribuido) > 0.01:
    raise ValueError("El OPEX distribuido no concilia con el original.")

# Guardar resultados
analisis_parques.to_csv(
    SALIDA / "analisis_mensual_parques.csv",
    index=False,
    encoding="utf-8-sig"
)

resumen_parques.to_csv(
    SALIDA / "resumen_financiero_parques.csv",
    encoding="utf-8-sig"
)

# =====================================================
# 9. GRÁFICA COMPARATIVA POR PARQUE
# =====================================================

fig, ax1 = plt.subplots(figsize=(12, 6))

posiciones = range(len(resumen_parques))
ancho = 0.35

ax1.bar(
    [x - ancho / 2 for x in posiciones],
    resumen_parques["Ingresos"] / 1_000_000,
    width=ancho,
    label="Ingresos"
)

ax1.bar(
    [x + ancho / 2 for x in posiciones],
    resumen_parques["OPEX ajustado"] / 1_000_000,
    width=ancho,
    label="OPEX ajustado"
)

ax1.set_ylabel("Millones de COP")
ax1.set_xticks(list(posiciones))
ax1.set_xticklabels(
    [nombre.title() for nombre in resumen_parques.index]
)
ax1.grid(axis="y", alpha=0.2)

# Eje secundario para margen
ax2 = ax1.twinx()

linea_margen, = ax2.plot(
    list(posiciones),
    resumen_parques["Margen estimado (%)"],
    marker="o",
    linestyle="--",
    color="green",
    linewidth=2,
    label="Margen estimado"
)

ax2.set_ylabel("Margen operativo estimado (%)")
ax2.yaxis.set_major_formatter(
    FuncFormatter(lambda valor, pos: f"{valor:.0f}%")
)

# Leyenda conjunta
barras, etiquetas = ax1.get_legend_handles_labels()

ax1.legend(
    barras + [linea_margen],
    etiquetas + ["Margen estimado"],
    loc="upper center",
    bbox_to_anchor=(0.5, -0.12),
    ncol=3
)

plt.title("Ingresos, OPEX y margen por parque - 2026")
plt.tight_layout()

plt.savefig(
    SALIDA / "comparativo_financiero_parques.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

# =====================================================
# 10. ANÁLISIS FINANCIERO POR PARQUE Y PROYECTO
# =====================================================

# Copias de los datos originales
ing_proy = ingresos.copy()

# Excluir Operaciones porque ya fue distribuido por parque
cos_proy = costos[costos["Parque"] != "operaciones"].copy()

# Normalizar códigos de proyecto
for df, columna in [
    (ing_proy, "PROYECTO"),
    (cos_proy, "Proyecto")
]:
    df["Proyecto_codigo"] = (
        df[columna].astype(str).str.strip().str.upper()
    )

# -----------------------------------------------------
# 10.1. Obtener nombres de proyectos
# -----------------------------------------------------

# Obtener nombres desde ambas fuentes, dando prioridad
# a ingresos cuando existe información coincidente.

nombres_ing = ing_proy[
    ["Parque", "Proyecto_codigo", "Nombre proyecto"]
].copy()

nombres_cos = cos_proy[
    ["Parque", "Proyecto_codigo", "Nombre proyecto"]
].copy()

nombres_ing["Prioridad"] = 1
nombres_cos["Prioridad"] = 2

nombres = pd.concat(
    [nombres_ing, nombres_cos],
    ignore_index=True
)

nombres["Nombre proyecto"] = (
    nombres["Nombre proyecto"]
    .astype("string")
    .str.strip()
)

# Excluir nombres vacíos
nombres = nombres[
    nombres["Nombre proyecto"].notna()
    & nombres["Nombre proyecto"].ne("")
].copy()

# Detectar nombres diferentes para un mismo código y parque
conflictos = (
    nombres.groupby(["Parque", "Proyecto_codigo"])[
        "Nombre proyecto"
    ].nunique()
)

if (conflictos > 1).any():
    print("\n--- ADVERTENCIA: NOMBRES DIFERENTES ---")
    print(conflictos[conflictos > 1])
    print("Se dará prioridad al nombre registrado en ingresos.")

# Seleccionar nombre según prioridad
nombres = (
    nombres.sort_values("Prioridad")
    .drop_duplicates(["Parque", "Proyecto_codigo"])
    [["Parque", "Proyecto_codigo", "Nombre proyecto"]]
)

# -----------------------------------------------------
# 10.2. Consolidar ingresos y OPEX directo
# -----------------------------------------------------

ingresos_proyecto = (
    ing_proy.groupby(
        ["Periodo", "Parque", "Proyecto_codigo"]
    )["INGRESO TOTAL"]
    .sum()
    .rename("Ingresos")
    .reset_index()
)

costos_proyecto = (
    cos_proy.groupby(
        ["Periodo", "Parque", "Proyecto_codigo"]
    )["Costo"]
    .sum()
    .rename("OPEX directo")
    .reset_index()
)

# Unir ingresos y costos sin excluir proyectos
# que únicamente tengan movimientos de costos.
detalle = pd.merge(
    ingresos_proyecto,
    costos_proyecto,
    on=["Periodo", "Parque", "Proyecto_codigo"],
    how="outer"
)

detalle[["Ingresos", "OPEX directo"]] = (
    detalle[["Ingresos", "OPEX directo"]].fillna(0)
)

# Agregar nombres de proyecto
detalle = detalle.merge(
    nombres,
    on=["Parque", "Proyecto_codigo"],
    how="left"
)

detalle["Nombre proyecto"] = (
    detalle["Nombre proyecto"]
    .fillna("Sin nombre registrado")
)

# -----------------------------------------------------
# 10.3. Distribuir Operaciones por proyecto
# -----------------------------------------------------

# Se conserva el prorrateo de Operaciones asignado
# previamente a cada parque y mes.

compartidos = analisis_parques[
    ["Periodo", "Parque", "OPEX asignado"]
].rename(
    columns={"OPEX asignado": "Compartido parque"}
)

detalle = detalle.merge(
    compartidos,
    on=["Periodo", "Parque"],
    how="left",
    validate="many_to_one"
)

detalle["Compartido parque"] = (
    detalle["Compartido parque"].fillna(0)
)

# Base de reparto: ingresos positivos de cada proyecto
detalle["Base reparto"] = detalle["Ingresos"].clip(lower=0)

total_base = detalle.groupby(
    ["Periodo", "Parque"]
)["Base reparto"].transform("sum")

# Participación de cada proyecto en el parque y mes
detalle["Participacion"] = (
    detalle["Base reparto"]
    / total_base.replace(0, float("nan"))
).fillna(0)

detalle["OPEX compartido proyecto"] = (
    detalle["Compartido parque"]
    * detalle["Participacion"]
)

# -----------------------------------------------------
# 10.4. Calcular resultados
# -----------------------------------------------------

detalle["OPEX ajustado"] = (
    detalle["OPEX directo"]
    + detalle["OPEX compartido proyecto"]
)

detalle["Resultado estimado"] = (
    detalle["Ingresos"] - detalle["OPEX ajustado"]
)

# Consolidar enero-septiembre por parque y proyecto
columnas_dinero = [
    "Ingresos",
    "OPEX directo",
    "OPEX compartido proyecto",
    "OPEX ajustado",
    "Resultado estimado"
]

resumen_proyectos = (
    detalle.groupby(
        ["Parque", "Proyecto_codigo", "Nombre proyecto"],
        as_index=False
    )[columnas_dinero].sum()
)

resumen_proyectos["Margen estimado (%)"] = (
    resumen_proyectos["Resultado estimado"]
    / resumen_proyectos["Ingresos"].replace(0, float("nan"))
    * 100
)

# Guardar detalle mensual
detalle.to_csv(
    SALIDA / "detalle_mensual_parque_proyecto.csv",
    index=False,
    encoding="utf-8-sig"
)

# Guardar consolidado general
resumen_proyectos.to_csv(
    SALIDA / "resumen_parque_proyecto.csv",
    index=False,
    encoding="utf-8-sig"
)


# =====================================================
# 11. TABLAS FINANCIERAS DE TODOS LOS PARQUES
# =====================================================

for parque in parques:

    tabla = resumen_proyectos[
        resumen_proyectos["Parque"] == parque
    ].copy()

    # Ordenar por ingresos descendentes
    tabla = tabla.sort_values(
        "Ingresos", ascending=False
    )

    # Calcular fila de totales
    totales = tabla[columnas_dinero].sum()

    margen_total = (
        totales["Resultado estimado"]
        / totales["Ingresos"] * 100
        if totales["Ingresos"] != 0
        else float("nan")
    )

    fila_total = {
        "Parque": parque,
        "Proyecto_codigo": "TOTAL PARQUE",
        "Nombre proyecto": "",
        **totales.to_dict(),
        "Margen estimado (%)": margen_total
    }

    tabla = pd.concat(
        [tabla, pd.DataFrame([fila_total])],
        ignore_index=True
    )

    # Guardar tabla numérica para Excel
    nombre_archivo = parque.replace(" ", "_")

    tabla.to_csv(
        SALIDA / f"proyectos_{nombre_archivo}.csv",
        index=False,
        encoding="utf-8-sig"
    )

    # Crear copia solo para visualización
    visual = tabla.drop(columns=["Parque"]).copy()

    # Formatear valores monetarios sin decimales
    for columna in columnas_dinero:
        visual[columna] = visual[columna].map(
            lambda valor: f"{valor:,.0f}"
        )

    # Porcentaje con dos decimales
    visual["Margen estimado (%)"] = (
        visual["Margen estimado (%)"].map(
            lambda valor: f"{valor:,.2f}%"
            if pd.notna(valor) else "N/A"
        )
    )

    # Nombres más cortos para presentación
    visual = visual.rename(columns={
        "Proyecto_codigo": "Código",
        "Nombre proyecto": "Nombre del proyecto",
        "OPEX compartido proyecto": "OPEX asignado",
        "Resultado estimado": "Resultado",
        "Margen estimado (%)": "Margen (%)"
    })

    print("\n" + "=" * 170)
    print(f"PARQUE ECOLÓGICO: {parque.upper()}")
    print("=" * 170)

    print(visual.to_string(index=False))


# =====================================================
# 12. CONCILIACIÓN DE COSTOS POR PARQUE
# =====================================================

opex_proyectos = resumen_proyectos.groupby("Parque")[
    "OPEX ajustado"
].sum()

opex_parques = resumen_parques["OPEX ajustado"]

diferencias = (
    opex_parques
    - opex_proyectos.reindex(
        opex_parques.index, fill_value=0
    )
)

print("\n" + "=" * 75)
print("CONCILIACIÓN DE COSTOS POR PARQUE")
print("=" * 75)

for parque, diferencia in diferencias.items():

    estado = (
        "CORRECTO"
        if abs(diferencia) < 0.01
        else "REVISAR"
    )

    print(
        f"{parque.title():<20}"
        f"{diferencia:>20,.2f}   {estado}"
    )

# Verificar meses sin base para distribuir Operaciones
sin_base = detalle[
    (total_base == 0)
    & (detalle["Compartido parque"].abs() > 0.01)
]

if not sin_base.empty:
    print(
        "\nADVERTENCIA: Existen meses y parques "
        "sin ingresos positivos para el prorrateo."
    )

# Validación final
if (diferencias.abs() > 0.01).any():
    print(
        "\nATENCIÓN: Existen diferencias. "
        "Revisar la distribución antes de interpretar."
    )
else:
    print("\nTodos los parques concilian correctamente.")

# =====================================================
# 13. ANÁLISIS EXPLORATORIO DE LA COMPOSICIÓN DEL OPEX
# =====================================================

# Trabajar con una copia para conservar los datos originales
costos_eda = costos.copy()

# Normalizar campos de clasificación
costos_eda["Categoria"] = (
    costos_eda["Item/ Costo"]
    .fillna("Sin clasificar")
    .astype(str)
    .str.strip()
)

costos_eda["Clasificacion"] = (
    costos_eda["Clasificación del costo"]
    .fillna("Sin clasificar")
    .astype(str)
    .str.strip()
)

costos_eda["Proyecto_codigo"] = (
    costos_eda["Proyecto"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# -----------------------------------------------------
# 13.1. Composición general del OPEX
# -----------------------------------------------------

opex_categoria = (
    costos_eda.groupby("Categoria")["Costo"]
    .agg(Registros="count", OPEX="sum")
    .sort_values("OPEX", ascending=False)
)

total_opex = costos_eda["Costo"].sum()

opex_categoria["Participacion (%)"] = (
    opex_categoria["OPEX"] / total_opex * 100
)

print("\n" + "=" * 85)
print("COMPOSICIÓN GENERAL DEL OPEX POR CATEGORÍA")
print("=" * 85)

print(opex_categoria.to_string(formatters={
    "Registros": "{:,.0f}".format,
    "OPEX": "{:,.0f}".format,
    "Participacion (%)": "{:.2f}%".format
}))

# -----------------------------------------------------
# 13.2. Clasificación general de los costos
# -----------------------------------------------------

opex_clasificacion = (
    costos_eda.groupby("Clasificacion")["Costo"]
    .agg(Registros="count", OPEX="sum")
    .sort_values("OPEX", ascending=False)
)

opex_clasificacion["Participacion (%)"] = (
    opex_clasificacion["OPEX"] / total_opex * 100
)

print("\n" + "=" * 85)
print("OPEX POR CLASIFICACIÓN DEL COSTO")
print("=" * 85)

print(opex_clasificacion.to_string(formatters={
    "Registros": "{:,.0f}".format,
    "OPEX": "{:,.0f}".format,
    "Participacion (%)": "{:.2f}%".format
}))

# -----------------------------------------------------
# 13.3. Composición del OPEX por parque
# -----------------------------------------------------

# Se analizan los costos registrados originalmente
# en cada planta, sin duplicar los prorrateos anteriores.

opex_parque_categoria = (
    costos_eda.groupby(["Parque", "Categoria"])["Costo"]
    .sum()
    .unstack(fill_value=0)
)

print("\n" + "=" * 85)
print("COMPOSICIÓN DEL OPEX POR PARQUE")
print("=" * 85)

for parque, fila in opex_parque_categoria.iterrows():

    tabla = fila.sort_values(ascending=False)

    print(f"\n--- {parque.upper()} ---")

    for categoria, valor in tabla.items():
        if valor != 0:
            print(f"{categoria:<35} {valor:>18,.0f}")

    print(f"{'TOTAL':<35} {tabla.sum():>18,.0f}")

# -----------------------------------------------------
# 13.4. Costos de los proyectos operativos generales
# -----------------------------------------------------

# Códigos generales confirmados previamente
proyectos_operativos = ["E61", "E60", "E62"]

costos_operativos = costos_eda[
    costos_eda["Proyecto_codigo"].isin(proyectos_operativos)
].copy()

resumen_operativos = (
    costos_operativos.groupby(
        ["Parque", "Proyecto_codigo", "Categoria"]
    )["Costo"]
    .sum()
    .reset_index()
    .sort_values(["Parque", "Proyecto_codigo", "Costo"],
                 ascending=[True, True, False])
)

print("\n" + "=" * 85)
print("COMPOSICIÓN DE LOS PROYECTOS OPERATIVOS GENERALES")
print("=" * 85)

for (parque, proyecto), grupo in resumen_operativos.groupby(
    ["Parque", "Proyecto_codigo"]
):
    print(f"\n--- {parque.upper()} | {proyecto} ---")

    for _, fila in grupo.iterrows():
        print(
            f"{fila['Categoria']:<35}"
            f"{fila['Costo']:>18,.0f}"
        )

    print(
        f"{'TOTAL':<35}"
        f"{grupo['Costo'].sum():>18,.0f}"
    )

# -----------------------------------------------------
# 13.5. Gráfica de composición general del OPEX
# -----------------------------------------------------

fig, ax = plt.subplots(figsize=(11, 6))

categorias_grafica = opex_categoria.sort_values("OPEX")

ax.barh(
    categorias_grafica.index,
    categorias_grafica["OPEX"] / 1_000_000
)

ax.set_xlabel("Millones de COP")
ax.set_ylabel("Categoría de costo")
ax.set_title("Composición del OPEX por categoría - 2026")
ax.grid(axis="x", alpha=0.25)

plt.tight_layout()

plt.savefig(
    SALIDA / "composicion_opex_categoria.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

# -----------------------------------------------------
# 13.6. Exportar resultados
# -----------------------------------------------------

opex_categoria.to_csv(
    SALIDA / "opex_por_categoria.csv",
    encoding="utf-8-sig"
)

opex_clasificacion.to_csv(
    SALIDA / "opex_por_clasificacion.csv",
    encoding="utf-8-sig"
)

opex_parque_categoria.to_csv(
    SALIDA / "opex_por_parque_categoria.csv",
    encoding="utf-8-sig"
)

resumen_operativos.to_csv(
    SALIDA / "opex_proyectos_operativos.csv",
    index=False,
    encoding="utf-8-sig"
)

# Verificación: el análisis no debe alterar el OPEX
diferencia = total_opex - opex_categoria["OPEX"].sum()

print("\n--- VALIDACIÓN FINAL DEL OPEX ---")
print(f"OPEX original:     {total_opex:,.0f}")
print(f"OPEX clasificado:  {opex_categoria['OPEX'].sum():,.0f}")
print(f"Diferencia:        {diferencia:,.2f}")

# =====================================================
# 14. DETALLE DE LA CATEGORÍA SERVICIOS
# =====================================================

servicios = costos_eda[
    costos_eda["Categoria"] == "11. SERVICIOS"
].copy()

# Distribución de Servicios por descripción
detalle_servicios = (
    servicios.groupby("Descripción")["Costo"]
    .sum()
    .sort_values(ascending=False)
)

total_servicios = detalle_servicios.sum()

tabla_servicios = pd.DataFrame({
    "OPEX": detalle_servicios,
    "Participación (%)": (
        detalle_servicios / total_servicios * 100
    )
})

print("\n--- PRINCIPALES CONCEPTOS DE SERVICIOS ---")

print(tabla_servicios.head(15).to_string(formatters={
    "OPEX": "{:,.0f}".format,
    "Participación (%)": "{:.2f}%".format
}))

# Distribución por planta de origen
servicios_parque = (
    servicios.groupby("Parque")["Costo"]
    .sum()
    .sort_values(ascending=False)
)

print("\n--- SERVICIOS POR PLANTA DE ORIGEN ---")

for parque, valor in servicios_parque.items():
    print(f"{parque.title():<22} {valor:>18,.0f}")

# Exportar información
tabla_servicios.to_csv(
    SALIDA / "detalle_servicios.csv",
    encoding="utf-8-sig"
)