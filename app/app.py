from flask import Flask, render_template, request
from scripts.teste1 import *
from pysus.online_data import sinasc, SINAN

app = Flask(__name__)

uf = 'PI'
disease1 = 'Sífilis Congênita'
disease2 = 'Sífilis em Gestante'
ano_ini = 2001
ano_fim = 2012

df_sinasc = download_sisinfo('SINASC', uf, ano_ini, ano_fim)
df_sinan_sif_cong = download_sisinfo('SINAN', disease1, ano_ini, ano_fim)
df_sinan_sif_gest = download_sisinfo('SINAN', disease2, ano_ini, ano_fim)

@app.route("/", methods=['GET', 'POST'])
def index():
    chart_type = request.args.get('chart_type', default='chart1')

    if chart_type == 'chart1':
        media_pesos_por_mes = calculo_media_peso2(df_sinasc)
        chart = create_bar_chart(media_pesos_por_mes)
    elif chart_type == 'chart2':
        taxa_sifilis_congenita = calcular_taxa_sifilis_congenita2(df_sinasc, df_sinan_sif_cong, df_sinan_sif_gest)
        chart = create_line_chart(taxa_sifilis_congenita)
    else:
        chart = None

    # Render the template with the selected chart
    return render_template("index.html", chart=chart)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
