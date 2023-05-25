from flask import Flask, render_template
from scripts.teste1 import *
from pysus.online_data import sinasc, SINAN

app = Flask(__name__)

#df = sinasc.download('PI', [2012, 2014])

uf = 'PI'
disease1 = 'Sífilis Congênita'
disease2 = 'Sífilis em Gestante'
ano_ini = 2001
ano_fim = 2012

df_sinasc = download_sisinfo('SINASC', uf, ano_ini, ano_fim)
df_sinan_sif_cong = download_sisinfo('SINAN', disease1, ano_ini, ano_fim)
df_sinan_sif_gest = download_sisinfo('SINAN', disease2, ano_ini, ano_fim)

# descrever o problema de uniformidade de base de dados
# focar em escrita
# 

@app.route("/")
def index():
    media_pesos_por_mes = calculo_media_peso2(df_sinasc)
    chart1 = create_bar_chart(media_pesos_por_mes)

    taxa_sifilis_congenita = calcular_taxa_sifilis_congenita2(df_sinasc, df_sinan_sif_cong, df_sinan_sif_gest)
    chart2 = create_line_chart(taxa_sifilis_congenita)

    # Render the template with the results and the charts
    return render_template("index.html", chart1=chart1, chart2=chart2)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)