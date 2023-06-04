from flask import Flask, render_template, request
from scripts.teste1 import *

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        chart_type = request.form['chart_type']
        if chart_type == 'chart1':
            uf = request.form['uf1']
            index = request.form['index1']
            ano_ini = int(request.form['ano_ini1'])
            ano_fim = int(request.form['ano_fim1']) if 'ano_fim1' in request.form and request.form['ano_fim1'].strip() != '' else None
            df_sinasc = download_sisinfo('SINASC', uf, ano_ini, ano_fim)
            media_pesos_por_mes = calculo_media(df_sinasc, index)
            chart = create_bar_chart(media_pesos_por_mes)
            return render_template("chart1.html", chart=chart)
        elif chart_type == 'chart2':
            uf = request.form['uf2']
            ano_ini = int(request.form['ano_ini2'])
            ano_fim = int(request.form['ano_fim2'])
            disease1 = request.form['disease1']
            disease2 = request.form['disease2']
            df_sinasc = download_sisinfo('SINASC', uf, ano_ini, ano_fim)
            df_sinan_sif_cong = download_sisinfo('SINAN', disease1, ano_ini, ano_fim)
            df_sinan_sif_gest = download_sisinfo('SINAN', disease2, ano_ini, ano_fim)
            taxa_sifilis_congenita = calcular_taxa(df_sinasc, df_sinan_sif_cong, df_sinan_sif_gest, uf)
            chart = create_line_chart(taxa_sifilis_congenita)
            return render_template("chart2.html", chart=chart)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)