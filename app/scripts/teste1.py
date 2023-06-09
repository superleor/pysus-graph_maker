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
        print(df_list, file=sys.stderr)
        return pd.concat(df_list, ignore_index=True)

def calculo_media(df, index):
    df[index] = pd.to_numeric(df[index], errors='coerce')
    df['DTNASC'] = pd.to_datetime(df['DTNASC'], format='%d%m%Y')
    df['YEAR'] = df['DTNASC'].dt.year
    df['MONTH'] = df['DTNASC'].dt.month
    
    if index == 'GESTACAO' or index == 'CONSULTAS':
        df = df[df[index] != 9] # remover dados ignorados
    
    media_por_mes_ano = df.groupby(['YEAR', 'MONTH'])[index].mean().reset_index()
    media_por_mes_ano[index] = media_por_mes_ano[index].apply(lambda x: round(x, 2))

    return media_por_mes_ano.set_index(['YEAR', 'MONTH']).to_dict()[index]


def calcular_taxa(df_sinasc, df_sinan1, df_sinan2, uf):
    df_disease1 = (df_sinan1.loc[df_sinan1['SG_UF'] == uf_dict[uf]]).rename(columns={'NU_ANO': 'ANO'})
    df_disease2 = (df_sinan2.loc[df_sinan2['SG_UF'] == uf_dict[uf]]).rename(columns={'NU_ANO': 'ANO'})

    df_sinasc['DTNASC'] = pd.to_datetime(df_sinasc['DTNASC'], format='%d%m%Y')
    df_sinasc['ANO'] = df_sinasc['DTNASC'].dt.year

    # Agrupa o número de casos de sífilis por ano no SINAN e no SINASC
    disease1_by_year_uf = df_disease1.groupby(['ANO']).size().rename('CASOS_SIFILIS_CONGENITA').reset_index()

    disease2_by_year_uf = df_disease2.groupby(['ANO']).size().rename('CASOS_SIFILIS_GESTACIONAL').reset_index()

    nascidos_vivos_por_ano_uf = df_sinasc.groupby(['ANO']).size().rename('NASCIDOS_VIVOS').reset_index()

    # Merge dos dados de casos de sífilis por ano com os de nascidos vivos por ano
    df_merged = pd.merge(disease1_by_year_uf, disease2_by_year_uf, on='ANO', how='outer')
    df_merged = pd.merge(df_merged, nascidos_vivos_por_ano_uf, on='ANO', how='outer')

    # Unindo as séries de dados em um dataframe
    df_merged = pd.concat([disease1_by_year_uf, disease2_by_year_uf, nascidos_vivos_por_ano_uf], axis=1)

    # Cálculo das taxas de sífilis congênita e gestacional por 1000 nascidos vivos
    df_merged['TAXA_SIFILIS_CONGENITA'] = df_merged['CASOS_SIFILIS_CONGENITA'] / df_merged['NASCIDOS_VIVOS'] * 1000
    df_merged['TAXA_SIFILIS_GESTACIONAL'] = df_merged['CASOS_SIFILIS_GESTACIONAL'] / df_merged['NASCIDOS_VIVOS'] * 1000
    df_merged = df_merged.loc[:,~df_merged.columns.duplicated()]

    return df_merged

def create_bar_chart(data):
    years = sorted(set(key[0] for key in data.keys()))
    months = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    
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

    layout = go.Layout(title='Média por mês', yaxis=dict(range=[min(y_values) - 1, max(y_values) + 1]), shapes=shapes)
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

uf_dict = {
    "AC": '12',
    "AL": '27',
    "AP": '16',
    "AM": '13',
    "BA": '29',
    "CE": '23',
    "DF": '53',
    "ES": '32',
    "GO": '52',
    "MA": '21',
    "MT": '51',
    "MS": '50',
    "MG": '31',
    "PA": '15',
    "PB": '25',
    "PR": '41',
    "PE": '26',
    "PI": '22',
    "RJ": '33',
    "RN": '24',
    "RS": '43',
    "RO": '11',
    "RR": '14',
    "SC": '42',
    "SP": '35',
    "SE": '28',
    "TO": '17'
}