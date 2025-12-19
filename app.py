import os
import re
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv

# Import modules
from database import get_conn
from queries import (
    SELECT_TIPO_CUSTO, SELECT_NOTE_SQL, 
    SELECT_CRT, SELECT_CTE, INSERT_RATEIO
)
from services import FileProcessor, ParseUtils

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "chave_secreta_dev")

DEFAULT_GRUPO = 1
DEFAULT_EMPRESA = 1

@app.route('/', methods=['GET'])
def index():
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(SELECT_TIPO_CUSTO)
            tipos = cur.fetchall()
        return render_template('index.html', tipos=tipos)
    except Exception as e:
        return f"Erro DB: {e}"

@app.route('/fetch_note', methods=['POST'])
def fetch_note():
    raw_cnpj = request.form.get('cnpj')
    cnpj = re.sub(r"\D", "", raw_cnpj) if raw_cnpj else None
    numero = request.form.get('numero')
    tipocusto_selected = request.form.get('tipocusto')

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(SELECT_TIPO_CUSTO)
        tipos = cur.fetchall()
        cur.execute(SELECT_NOTE_SQL, {'numero': int(numero), 'cnpj': cnpj})
        note = cur.fetchone()

    if not note:
        flash('Nota fiscal não encontrada.', 'danger')
    return render_template('index.html', tipos=tipos, note=note, tipocusto_selected=tipocusto_selected)

@app.route('/upload', methods=['POST'])
def upload():
    raw_cnpj = request.form.get('cnpj')
    cnpj = re.sub(r"\D", "", raw_cnpj) if raw_cnpj else None
    numero = request.form.get('numero')
    tipocusto = request.form.get('tipocusto')
    valor_padrao_float = ParseUtils.parse_float_safe(request.form.get('valor_padrao', '0'))

    file = request.files.get('file')
    if not file: return redirect(url_for('index'))

    try:
        docs_dict, read_log = FileProcessor.extract_documents_with_values(file)
    except Exception as e:
        flash(f'Erro arquivo: {e}', 'danger')
        return redirect(url_for('index'))

    if not docs_dict:
        flash('Nenhum documento válido encontrado.', 'danger')
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(SELECT_NOTE_SQL, {'numero': int(numero), 'cnpj': cnpj})
            note = cur.fetchone()
            cur.execute(SELECT_TIPO_CUSTO)
            tipos = cur.fetchall()
        return render_template('index.html', tipos=tipos, note=note, tipocusto_selected=tipocusto)

    log_msg = " | ".join(read_log)
    flash(f"Leitura concluída! {log_msg}", "info")

    allocations = []
    
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(SELECT_NOTE_SQL, {'numero': int(numero), 'cnpj': cnpj})
        note = cur.fetchone()
        cur.execute(SELECT_TIPO_CUSTO)
        tipos = cur.fetchall()

        for doc_str, data in docs_dict.items():
            
            # --- LÓGICA DE PRIORIDADE ---
            if data['sum'] > 0.001:
                final_val = data['sum']
            else:
                final_val = data['count'] * valor_padrao_float

            cur.execute(SELECT_CRT, {'numero': doc_str})
            doc_data = cur.fetchone()
            
            if not doc_data:
                if doc_str.isdigit():
                    cur.execute(SELECT_CTE, {'numero': doc_str})
                    doc_data = cur.fetchone()

            if doc_data:
                allocations.append({
                    'found': True,
                    'doc_numero': doc_str,
                    'tipo': doc_data['origem_tipo'],
                    'valor': "{:.2f}".format(final_val), 
                    'doc_data': doc_data 
                })
            else:
                allocations.append({
                    'found': False,
                    'doc_numero': doc_str,
                    'tipo': '?',
                    'valor': "{:.2f}".format(final_val), 
                    'doc_data': {}
                })

    allocations.sort(key=lambda x: (not x['found'], x['tipo'], x['doc_numero']))

    return render_template('index.html', tipos=tipos, note=note, allocations=allocations, tipocusto_selected=tipocusto)

@app.route('/save', methods=['POST'])
def save():
    count = int(request.form.get('count', 0))
    raw_cnpj = request.form.get('cnpj')
    cnpj = re.sub(r"\D", "", raw_cnpj) if raw_cnpj else None
    numero = request.form.get('numero')
    serie = request.form.get('serie')
    dtemissao = request.form.get('dtemissao')
    tipocusto = request.form.get('tipocusto')

    items_to_save = []
    total_submit = 0.0

    for i in range(count):
        if request.form.get(f'found_{i}') != '1': continue
        
        val_str = request.form.get(f'allocation_val_{i}')
        valor = ParseUtils.parse_float_safe(val_str)
        if valor <= 0: continue

        total_submit += valor
        
        items_to_save.append({
            'grupo': DEFAULT_GRUPO,
            'empresa': DEFAULT_EMPRESA,
            'cnpjcpfcodigo': cnpj,
            'dtemissao': dtemissao,
            'serie': serie,
            'numero': int(numero),
            'valor': valor,
            'tipocusto': tipocusto,
            'doc_tipodoc': request.form.get(f'doc_tipodoc_{i}'),
            'doc_grupo': request.form.get(f'doc_grupo_{i}'),
            'doc_empresa': request.form.get(f'doc_empresa_{i}'),
            'doc_filial': request.form.get(f'doc_filial_{i}'),
            'doc_unidade': request.form.get(f'doc_unidade_{i}'),
            'doc_dtemissao': request.form.get(f'doc_dtemissao_{i}'),
            'doc_dif_seq': request.form.get(f'doc_dif_seq_{i}'),
            'doc_seq': request.form.get(f'doc_seq_{i}'),     
            'doc_peso': request.form.get(f'doc_peso_{i}'),
            'doc_serie': request.form.get(f'doc_serie_{i}')   
        })

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(SELECT_NOTE_SQL, {'numero': int(numero), 'cnpj': cnpj})
        note_data = cur.fetchone()
        
        if not note_data:
             flash('Erro ao validar nota fiscal.', 'danger')
             return redirect(url_for('index'))

        total_nf = float(note_data['valortotalnotafiscal'])
        diff = abs(total_nf - total_submit)
        
        if diff > 0.01:
            flash(f'ERRO: Divergência de valores. NF: {total_nf} vs Rateio: {total_submit}', 'danger')
            return redirect(url_for('index'))

        inserted_count = 0
        for params in items_to_save:
            for k, v in params.items():
                if v == '' or v == 'None': params[k] = None
            
            cur.execute(INSERT_RATEIO, params)
            inserted_count += 1
        conn.commit()

    flash(f'Sucesso! {inserted_count} rateios gravados.', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)