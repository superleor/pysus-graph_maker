from __future__ import print_function
from pysus.online_data import sinasc, SINAN, parquets_to_dataframe
import sys
import plotly.graph_objs as go
import pandas as pd

""" df = download('PI', 2012)
df2 = download('PI', 2019)
df3 = download('SC', 2019) """

""" def calculo_media_peso(df, by_month = True):
    pesos = pd.to_numeric(df['PESO'], errors='coerce')
    dtnascs = df['DTNASC']

    if by_month:
        pesos_por_mes = defaultdict(lambda: {"total": 0.0, "count": 0})
    else:
        pesos_por_mes = defaultdict(lambda: {"total": 0.0, "count": 0, "year": None})


    for peso, dtnasc in zip(pesos, dtnascs):
        if not pd.isna(peso):
            if by_month:
                periodo = dtnasc[2:4]
            else:
                periodo = dtnasc[4:]
            pesos_por_mes[periodo]["total"] += peso
            pesos_por_mes[periodo]["count"] += 1
            if not by_month:
                pesos_por_mes[periodo]["year"] = dtnasc[4:]

    media_pesos_por_mes = {}
    for periodo, data in pesos_por_mes.items():
        if by_month:
            media_pesos_por_mes[periodo] = data["total"] / data["count"]
        else:
            media_pesos_por_mes[data["year"]] = data["total"] / data["count"]

    return media_pesos_por_mes """

# interessante mencionar a mudança para pandas no texto e do docker (timeline)
# generalizar baseado em input do usuário (não necessariamente em código)

def download_sisinfo(sisinfo, uf_or_disease, ano_ini, ano_fim=None):
    if sisinfo == 'SINASC':
        download_func = sinasc.download
    elif sisinfo == 'SINAN':
        download_func = SINAN.download
    else:
        raise ValueError('Sistema de informação inválido')
    
    df_list = []
    
    if ano_fim is None:
        df = download_func(uf_or_disease, ano_ini)
        if df == ():
            return df_list
        df = parquets_to_dataframe(df)
        df_list.append(df)
    else:
        for ano in range(ano_ini, ano_fim+1):
            print(ano, file=sys.stderr)
            df = download_func(uf_or_disease, ano)
            if df == ():
                continue
            df = parquets_to_dataframe(df)
            df_list.append(df)
    
    if df_list == []:
        return df_list
    else: 
        return pd.concat(df_list, ignore_index=True)

def calculo_media_peso2(df):
    df['PESO'] = pd.to_numeric(df['PESO'], errors='coerce')
    df['DTNASC'] = pd.to_datetime(df['DTNASC'], format='%d%m%Y')
    df['MES'] = df['DTNASC'].dt.month
    media_por_mes = df.groupby('MES')['PESO'].mean()
    return media_por_mes.to_dict()

def calcular_taxa_sifilis_congenita2(df_sinasc, df_sinan1, df_sinan2):
    df_sifilis_cong_piaui = (df_sinan1.loc[df_sinan1['SG_UF'] == '22']).rename(columns={'NU_ANO': 'ANO'}) #22 é o código do Piauí
    df_sifilis_gest_piaui = (df_sinan2.loc[df_sinan2['SG_UF'] == '22']).rename(columns={'NU_ANO': 'ANO'})

    df_sinasc['DTNASC'] = pd.to_datetime(df_sinasc['DTNASC'], format='%d%m%Y')
    df_sinasc['ANO'] = df_sinasc['DTNASC'].dt.year

    # Agrupa o número de casos de sífilis por ano no SINAN e no SINASC
    sifilis_cong_por_ano_uf = df_sifilis_cong_piaui.groupby(['ANO']).size().rename('CASOS_SIFILIS_CONGENITA').reset_index()

    sifilis_gestacional_por_ano_uf = df_sifilis_gest_piaui.groupby(['ANO']).size().rename('CASOS_SIFILIS_GESTACIONAL').reset_index()

    nascidos_vivos_por_ano_uf = df_sinasc.groupby(['ANO']).size().rename('NASCIDOS_VIVOS').reset_index()

    # Merge dos dados de casos de sífilis por ano com os de nascidos vivos por ano
    df_merged = pd.merge(sifilis_cong_por_ano_uf, sifilis_gestacional_por_ano_uf, on='ANO', how='outer')
    df_merged = pd.merge(df_merged, nascidos_vivos_por_ano_uf, on='ANO', how='outer')

    # Unindo as séries de dados em um dataframe
    df_merged = pd.concat([sifilis_cong_por_ano_uf, sifilis_gestacional_por_ano_uf, nascidos_vivos_por_ano_uf], axis=1)

    # Cálculo das taxas de sífilis congênita e gestacional por 1000 nascidos vivos
    df_merged['TAXA_SIFILIS_CONGENITA'] = df_merged['CASOS_SIFILIS_CONGENITA'] / df_merged['NASCIDOS_VIVOS'] * 1000
    df_merged['TAXA_SIFILIS_GESTACIONAL'] = df_merged['CASOS_SIFILIS_GESTACIONAL'] / df_merged['NASCIDOS_VIVOS'] * 1000
    df_merged = df_merged.loc[:,~df_merged.columns.duplicated()]

    return df_merged

    #print((df_sifilis_piaui/nascidos_vivos), file=sys.stderr)

def create_bar_chart(data):
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    x_values = [months[i-1] for i in data.keys()]
    y_values = list(data.values())

    trace = go.Bar(x=x_values, y=y_values)
    data = [trace]

    layout = go.Layout(title='Average weight by month')
    fig = go.Figure(data=data, layout=layout)

    return fig.to_html(full_html=False)

def create_line_chart(df):
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['ANO'], y=df['TAXA_SIFILIS_CONGENITA'],
        mode='lines', name='Taxa de Sífilis Congênita'
    ))
    
    fig.add_trace(go.Scatter(
        x=df['ANO'], y=df['TAXA_SIFILIS_GESTACIONAL'],
        mode='lines', name='Taxa de Sífilis em Gestante'
    ))

    fig.update_layout(
        title='Taxa de Sífilis Congênita e em Gestante por 1000 nascidos vivos',
        xaxis_title='Ano',
        yaxis_title='Taxa por 1000 nascidos vivos'
    )
    
    return fig.to_html(full_html=False)

""" 
#peso medio por mes entre 2012 e 2019 no PI
media_pesos_por_mes1 = calculo_media_peso(df) #PI, 2012
media_pesos_por_mes2 = calculo_media_peso(df2) #PI, 2019

#PESO MEDIO DE 2019 ENTRE pi e sc
media_pesos_pandas1 = calculo_media_peso2(df) #PI, 2019
media_pesos_pandas2 = calculo_media_peso2(df2) #SC, 2019
 """
""" print("Media de pesos por mês:")
for periodo in sorted(media_pesos_por_mes1.keys()):
    print(f"{periodo}: {(media_pesos_por_mes1[periodo] - media_pesos_por_mes2[periodo]):.2f} gramas") """ #positivo: 2012 >, negativo: 2019 >

""" print("Media de pesos por ano:")
for periodo in sorted(media_pesos_por_mes1.keys()):
    print(f"{periodo}: {(media_pesos_por_mes1[periodo] - media_pesos_por_mes2[periodo]):.2f} gramas") """ #positivo: PI >, negativo: SC >
""" 
for mes, media in media_pesos_pandas1.items():
    print(f'Mês {mes}: {media:.2f}') """
#df2 = pd.DataFrame({"peso":peso, "dtNasc":dtNasc})
#df2.to_csv("teste1.csv",index=False)