from flask import Flask, render_template, request, redirect
from scripts.teste1 import *
from pysus.online_data import sinasc, SINAN

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        chart_type = request.form['chart_type']
        if chart_type == 'chart1':
            uf = request.form['uf']
            ano_ini = int(request.form['ano_ini'])
            ano_fim = int(request.form['ano_fim']) if 'ano_fim' in request.form and request.form['ano_fim'].strip() != '' else None
            return redirect(f'/chart1?uf={uf}&ano_ini={ano_ini}&ano_fim={ano_fim}')
        elif chart_type == 'chart2':
            return redirect('/chart2')
    return render_template("index.html")

@app.route("/chart1")
def generate_chart1():
    uf = request.args.get('uf')
    ano_ini = int(request.args.get('ano_ini'))
    ano_fim = int(request.form['ano_fim']) if 'ano_fim' in request.form and request.form['ano_fim'].strip() != '' else None
    df_sinasc = download_sisinfo('SINASC', uf, ano_ini, ano_fim)
    media_pesos_por_mes = calculo_media_peso2(df_sinasc)
    chart = create_bar_chart(media_pesos_por_mes)
    
    return render_template("chart1.html", chart=chart)
""" 
@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        chart_type = request.form['chart_type']
        if chart_type == 'chart1':
            return redirect('/chart1')
        elif chart_type == 'chart2':
            return redirect('/chart2')
    return render_template("index.html")

@app.route("/chart1")
def generate_chart1():
    uf = 'PI'
    ano_ini = 2011
    df_sinasc = download_sisinfo('SINASC', uf, ano_ini)
    media_pesos_por_mes = calculo_media_peso2(df_sinasc)
    chart = create_bar_chart(media_pesos_por_mes)
    return render_template("chart1.html", chart=chart)
 """
@app.route("/chart2")
def generate_chart2():
    uf = 'PI'
    disease1 = 'Sífilis Congênita'
    disease2 = 'Sífilis em Gestante'
    ano_ini = 2001
    ano_fim = 2012
    df_sinasc = download_sisinfo('SINASC', uf, ano_ini, ano_fim)
    df_sinan_sif_cong = download_sisinfo('SINAN', disease1, ano_ini, ano_fim)
    df_sinan_sif_gest = download_sisinfo('SINAN', disease2, ano_ini, ano_fim)
    taxa_sifilis_congenita = calcular_taxa_sifilis_congenita2(df_sinasc, df_sinan_sif_cong, df_sinan_sif_gest)
    chart = create_line_chart(taxa_sifilis_congenita)
    return render_template("chart2.html", chart=chart)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
