from __future__ import print_function
from pysus.online_data import sinasc, SINAN, parquets_to_dataframe
import sys
import plotly.graph_objs as go
import pandas as pd

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
    df['YEAR'] = df['DTNASC'].dt.year
    df['MONTH'] = df['DTNASC'].dt.month
    media_por_mes_ano = df.groupby(['YEAR', 'MONTH'])['PESO'].mean()
    return media_por_mes_ano.to_dict()

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
    years = sorted(set(key[0] for key in data.keys()))
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    
    x_values = []
    y_values = []
    separators = []

    for year in years:
        x_values.extend([months[key[1] - 1] + f" ({year})" for key in data.keys() if key[0] == year])
        y_values.extend(list(data[key] for key in data.keys() if key[0] == year))
        separators.append(len(x_values) - 0.5)
    
    shapes = []
    for separator in separators:
        shapes.append({'type': 'line', 'xref': 'x', 'yref': 'paper', 'x0': separator, 'x1': separator, 'y0': 0, 'y1': 1, 'line': {'color': 'black', 'width': 1}})

    trace = go.Bar(x=x_values, y=y_values)
    data = [trace]

    layout = go.Layout(title='Average weight by month', yaxis=dict(range=[min(y_values) - 1, max(y_values) + 1]), shapes=shapes)
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