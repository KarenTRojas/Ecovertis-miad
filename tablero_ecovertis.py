"""Tablero de Ecovertis — Entrega 2. Requiere Dash/Plotly.

Arrancar: python tablero_ecovertis.py
Abrir: http://127.0.0.1:8050
"""
from __future__ import annotations
import csv
from collections import defaultdict
from pathlib import Path

from dash import Dash, Input, Output, dcc, html
import plotly.graph_objects as go
from plotly.subplots import make_subplots

BASE = Path(__file__).resolve().parent
DATA = BASE / 'resultados'
PARKS = ['acacias','neiva','puerto gaitan','putumayo','tanques']
MONTH_NAMES = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']


def rows(name):
    p=DATA/name
    if not p.exists():
        raise FileNotFoundError(f"Falta {p}. Ejecuta primero modelos_entrega2.py.")
    with open(p,encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))

HIST=rows('analisis_mensual_parques.csv')
DETAIL=rows('detalle_mensual_parque_proyecto.csv')
FORECAST=rows('pronostico_oct_dic_2026.csv')
COSTCAT=rows('opex_por_categoria.csv')
COSTPARK=rows('opex_por_parque_categoria.csv')
COMPARE=rows('comparacion_modelos.csv')


def num(x):
    try: return float(x)
    except (TypeError,ValueError): return 0.0


def mes(s):return int(str(s).split('.')[0])

def cop_m(v):
    # 1.234,5 M COP (separadores colombianos)
    txt=f'{v/1e6:,.1f}'
    return txt.replace(',','X').replace('.',',').replace('X','.')+' M'


def money(v):return '$'+cop_m(v)

def park_label(v):return {'acacias':'Acacías','neiva':'Neiva','puerto gaitan':'Puerto Gaitán','putumayo':'Putumayo','tanques':'Tanques'}.get(v,v.title())


def build_historical(parque, proyecto):
    # Se prioriza el detalle de proyectos si hay uno elegido; si no, se usa el consolidado conciliado.
    origin = DETAIL if proyecto != 'todos' else HIST
    by=defaultdict(lambda:[0.0,0.0])
    for r in origin:
        if parque != 'todos' and r['Parque']!=parque:continue
        if proyecto != 'todos' and r.get('Proyecto_codigo')!=proyecto:continue
        m=mes(r['Periodo'])
        by[m][0] +=num(r['Ingresos'])
        by[m][1] +=num(r['OPEX ajustado'])
    return by


def build_forecast(parque, proyecto):
    by=defaultdict(lambda:[0.0,0.0])
    if proyecto != 'todos':return by
    for r in FORECAST:
        if parque!='todos' and r['parque']!=parque:continue
        m=int(r['mes'])
        j=0 if r['variable']=='ingresos' else 1
        by[m][j]+=num(r['pronostico_cop'])
    return by


def finance_sum(vals):
    ing=sum(x[0] for x in vals.values());cos=sum(x[1] for x in vals.values());
    return ing,cos,ing-cos,(ing-cos)/ing*100 if ing>0 else None


def card(title, value, note):
    return html.Div(className='kpi',children=[html.Div(title,className='kpi-label'),html.Div(value,className='kpi-value'),html.Div(note,className='kpi-note')])


def evolution_chart(history,forecast,mostrar):
    fig=make_subplots(specs=[[{'secondary_y':True}]])
    if mostrar!='proyeccion':
        months=sorted(history)
        fig.add_trace(go.Bar(x=[MONTH_NAMES[m-1] for m in months],y=[history[m][0]/1e6 for m in months],name='Ingresos históricos',marker_color='#2778b5'),secondary_y=False)
        fig.add_trace(go.Bar(x=[MONTH_NAMES[m-1] for m in months],y=[history[m][1]/1e6 for m in months],name='OPEX histórico',marker_color='#e49b4b'),secondary_y=False)
        fig.add_trace(go.Scatter(x=[MONTH_NAMES[m-1] for m in months],y=[(history[m][0]-history[m][1])/history[m][0]*100 if history[m][0]>0 else None for m in months],name='Margen histórico (%)',mode='lines+markers',line={'color':'#147b64','width':3}),secondary_y=True)
    if mostrar!='historico' and forecast:
        months=sorted(forecast)
        fig.add_trace(go.Bar(x=[MONTH_NAMES[m-1] for m in months],y=[forecast[m][0]/1e6 for m in months],name='Ingresos pronosticados',marker_color='#9cb8c0'),secondary_y=False)
        fig.add_trace(go.Bar(x=[MONTH_NAMES[m-1] for m in months],y=[forecast[m][1]/1e6 for m in months],name='OPEX pronosticado',marker_color='#c3cbc9'),secondary_y=False)
        fig.add_trace(go.Scatter(x=[MONTH_NAMES[m-1] for m in months],y=[(forecast[m][0]-forecast[m][1])/forecast[m][0]*100 if forecast[m][0]>0 else None for m in months],name='Margen proyectado (%)',mode='lines+markers',line={'color':'#798d95','width':3,'dash':'dash'}),secondary_y=True)
    fig.update_layout(height=410,margin={'l':40,'r':48,'t':20,'b':50},barmode='group',legend={'orientation':'h','y':-0.18},plot_bgcolor='#fff',paper_bgcolor='#fff',font={'family':'Arial','color':'#1b3d32'})
    fig.update_yaxes(title_text='Millones de COP',secondary_y=False,gridcolor='#e6efea',rangemode='tozero')
    fig.update_yaxes(title_text='Margen (%)',secondary_y=True,showgrid=False)
    return fig


def cost_chart(parque):
    values={}
    if parque=='todos':
        for r in COSTCAT:values[r['Categoria']]=num(r['OPEX'])
    else:
        for r in COSTPARK:
            if r['Parque']==parque:
                values={k:num(v) for k,v in r.items() if k!='Parque'}
    data=sorted(((k,v) for k,v in values.items() if v>0),key=lambda x:x[1],reverse=True)[:8]
    fig=go.Figure(go.Bar(x=[v/1e6 for k,v in data][::-1],y=[k for k,v in data][::-1],orientation='h',marker_color='#147b64'))
    fig.update_layout(height=370,margin={'l':10,'r':15,'t':8,'b':55},plot_bgcolor='#fff',paper_bgcolor='#fff',xaxis_title='Millones de COP',font={'family':'Arial','color':'#1b3d32','size':11})
    fig.update_xaxes(gridcolor='#e6efea')
    return fig


app=Dash(__name__,title='Ecovertis | Inteligencia financiera')
app.layout=html.Div([
    html.Header([html.H1('◈ Ecovertis  |  Inteligencia financiera'),html.Div('Prototipo analítico · Entrega 2 · 2026',className='header-subtitle')],className='header'),
    html.Main([
        html.H2('Ejecución financiera y proyección de cierre'),
        html.P('Ingresos y costos de enero a septiembre de 2026. Pronósticos experimentales de octubre a diciembre, diferenciados de los registros ejecutados.'),
        html.Div([
            html.Div([html.Label('Parque ecológico'),dcc.Dropdown(id='parque',options=[{'label':'Todos los parques','value':'todos'}]+[{'label':park_label(p),'value':p} for p in PARKS],value='todos',clearable=False)],className='filter'),
            html.Div([html.Label('Proyecto'),dcc.Dropdown(id='proyecto',options=[{'label':'Todos los proyectos','value':'todos'}],value='todos',clearable=False)],className='filter'),
            html.Div([html.Label('Período a visualizar'),dcc.Dropdown(id='periodo',options=[{'label':'Histórico y pronóstico','value':'ambos'},{'label':'Solo histórico','value':'historico'},{'label':'Solo pronóstico','value':'proyeccion'}],value='ambos',clearable=False)],className='filter'),
        ],className='filters'),
        html.Div(id='kpis',className='kpis'),
        html.Div([
            html.Section([html.H3('Evolución mensual'),dcc.Graph(id='evolucion',config={'displaylogo':False}),html.Div(id='nota-modelos',className='note')],className='panel wide'),
            html.Section([html.H3('Composición del OPEX'),dcc.Graph(id='costos',config={'displaylogo':False}),html.P('Al filtrar un parque, la composición muestra costos directos antes de repartir Operaciones. Las tarjetas utilizan OPEX ajustado.',className='muted')],className='panel')
        ],className='charts'),
        html.Section([html.H3('Comparación de modelos (agosto–septiembre de 2026)'),html.Div(id='model_table'),html.P('Validación preliminar de solo dos meses. Los pronósticos son experimentales y no presupuestos aprobados.',className='muted')],className='panel'),
        html.P('Resultado operativo estimado = ingresos – OPEX ajustado; no equivale a utilidad neta. Fuente: base simulada de Ecovertis y análisis de la Entrega 1.',className='footer')
    ])
])

@app.callback(Output('proyecto','options'),Output('proyecto','value'),Input('parque','value'))
def proyectos_de_parque(parque):
    opts={}
    for r in DETAIL:
        if parque=='todos' or r['Parque']==parque:
            ident=r['Proyecto_codigo']
            nombre=(r.get('Nombre proyecto') or '').strip()
            opts[ident]=f'{ident} · {nombre}' if nombre else ident
    return ([{'label':'Todos los proyectos','value':'todos'}]+[{'label':lab,'value':key} for key,lab in sorted(opts.items())],'todos')

@app.callback(Output('kpis','children'),Output('evolucion','figure'),Output('costos','figure'),Output('nota-modelos','children'),Output('model_table','children'), Input('parque','value'),Input('proyecto','value'),Input('periodo','value'))
def actualizar(parque,proyecto,periodo):
    hist=build_historical(parque,proyecto)
    pron=build_forecast(parque,proyecto)
    if periodo=='historico':used=hist;nota='Histórico: enero a septiembre de 2026.'
    elif periodo=='proyeccion':used=pron;nota='Pronósticos experimentales: octubre a diciembre de 2026.'
    else:
        used={**hist,**pron};nota='Histórico enero–septiembre; pronóstico octubre–diciembre, en gris.'
    if proyecto!='todos':
        nota+=' No hay pronóstico por proyecto: la muestra mensual es insuficiente para justificar ese nivel de desagregación.'
    ing,cost,result,margin=finance_sum(used)
    cards=[card('Ingresos',money(ing),'COP · período seleccionado'),card('OPEX ajustado',money(cost),'COP · incluye distribución de Operaciones'),card('Resultado estimado',money(result),'Ingresos menos OPEX ajustado'),card('Margen estimado',f'{margin:,.1f}%'.replace('.',',') if margin is not None else 'N/D','No representa utilidad neta')]
    fig=evolution_chart(hist,pron,periodo)
    table=html.Table([html.Thead(html.Tr([html.Th('Variable'),html.Th('Modelo'),html.Th('MAE (M COP)'),html.Th('WAPE')]))]+[html.Tbody([html.Tr([html.Td('Ingresos' if r['serie']=='ingresos' else 'OPEX'),html.Td(r['modelo']),html.Td(r['mae_millones_cop']),html.Td(f"{r['wape_pct']}%")]) for r in COMPARE])])
    return cards,fig,cost_chart(parque),nota,table

if __name__=='__main__':
    app.run_server(host='127.0.0.1',port=8050,debug=False)
