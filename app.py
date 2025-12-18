import os
import re
import math
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
import psycopg2.extras
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# --- Configurações de Banco de Dados ---
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "chave_secreta_dev")

DEFAULT_GRUPO = 1
DEFAULT_EMPRESA = 1

# --- SQLs ---

SELECT_TIPO_CUSTO = """
    SELECT tipocusto.codigo, tipocusto.descricao 
    FROM tipocusto 
    WHERE tipocusto.ativoinativo = '1' and tipocusto.grupo = '1' and tipocusto.empresa = '1'
    ORDER BY codigo;
"""

SELECT_NOTE_SQL = """
    SELECT DISTINCT
         nfe.grupo, nfe.empresa, nfe.filial, nfe.unidade
        ,fnc_formata_cnpjcpfcod(nfe.cnpjcpfcodigo) AS cnpjcpfcodigoformatado
        ,initcap(cad.razaosocial) AS razaosocial
        ,nfe.cnpjcpfcodigo, nfe.serie, nfe.numero, nfe.dtemissao
        ,nfe.valortotalnotafiscal
    FROM notafiscalentrada nfe
    JOIN cadastro cad ON cad.codigo = nfe.cnpjcpfcodigo
    WHERE nfe.grupo = 1 AND nfe.empresa = 1
      AND nfe.numero = %(numero)s
      AND nfe.cnpjcpfcodigo = %(cnpj)s
    ORDER BY nfe.dtemissao DESC LIMIT 1;
"""

SELECT_CRT = """
    SELECT 
        'CRT' as origem_tipo,
        crt.tipodocumento as doc_tipodoc, 
        crt.grupo as doc_grupo, 
        crt.empresa as doc_empresa, 
        crt.filial as doc_filial, 
        crt.unidade as doc_unidade, 
        crt.dtemissao as doc_dtemissao, 
        crt.diferenciadorsequencia as doc_dif_seq, 
        crt.sequencia as doc_seq, 
        crt.pesobruto as doc_peso, 
        crt.numero as doc_numero_real,
        crt.serienotafiscal as doc_serie
    FROM crt 
    WHERE crt.numero = %(numero)s
    LIMIT 1;
"""

SELECT_CTE = """
    SELECT 
        'CTE' as origem_tipo,
        conhecimento.tipodocumento as doc_tipodoc,
        conhecimento.grupo as doc_grupo,
        conhecimento.empresa as doc_empresa,
        conhecimento.filial as doc_filial,
        conhecimento.unidade as doc_unidade,
        conhecimento.dtemissao as doc_dtemissao,
        conhecimento.diferenciadornumero as doc_dif_seq,
        conhecimento.numero as doc_seq,
        conhecimento.pesobruto as doc_peso,
        conhecimento.numero as doc_numero_real,
        conhecimento.serie as doc_serie
    FROM conhecimento
    WHERE conhecimento.numero = %(numero)s
    LIMIT 1;
"""

INSERT_RATEIO = """
    INSERT INTO notafiscalentrada_rateiodocumento 
     (grupo, empresa, cnpjcpfcodigo, dtemissao, serie, numero, sequencia, 
      dtinc, dtalt, 
      tipodocumento, grupodocumento, empresadocumento, filialdocumento, unidadedocumento, 
      cnpjcpfcodigodocumento, dtemissaodocumento, diferenciadornumerodocumento, 
      seriedocumento, numerosequenciadocumento, pesodocumento, 
      valor, tipocusto)
     
    VALUES (
        %(grupo)s, %(empresa)s, %(cnpjcpfcodigo)s, %(dtemissao)s, %(serie)s, %(numero)s,
        COALESCE((SELECT MAX(sequencia) FROM notafiscalentrada_rateiodocumento 
                  WHERE grupo=%(grupo)s AND empresa=%(empresa)s 
                  AND cnpjcpfcodigo=%(cnpjcpfcodigo)s AND dtemissao=%(dtemissao)s 
                  AND serie=%(serie)s AND numero=%(numero)s), 0) + 1,
        NOW(), NULL,
        
        %(doc_tipodoc)s,
        %(doc_grupo)s,
        %(doc_empresa)s,
        %(doc_filial)s,
        %(doc_unidade)s,
        NULL, 
        %(doc_dtemissao)s,
        %(doc_dif_seq)s, 
        %(doc_serie)s,
        %(doc_seq)s,
        %(doc_peso)s,    
        %(valor)s, 
        %(tipocusto)s
    );
"""

def get_conn():
    return psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, 
        host=DB_HOST, port=DB_PORT, 
        cursor_factory=psycopg2.extras.RealDictCursor
    )

def _parse_float_safe(val_str):
    if val_str is None: return 0.0
    if isinstance(val_str, (float, int)):
        if isinstance(val_str, float) and (math.isnan(val_str) or math.isinf(val_str)): return 0.0
        return float(val_str)
    val_str = str(val_str).strip()
    if not val_str or val_str.lower() in ['nan', 'none', 'null', '']: return 0.0
    try:
        if ',' in val_str: val_str = val_str.replace('.', '').replace(',', '.')
        val = float(val_str)
        if math.isnan(val) or math.isinf(val): return 0.0
        return val
    except ValueError:
        return 0.0

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

def _clean_cell_value(raw_val):
    if not raw_val: return []
    val_str = str(raw_val).strip().upper()
    if val_str in ['#REF!', 'NAN', 'None', '', 'SEM CRT', 'SEM CTE']: return []
    val_str = re.sub(r'[\/\-\\\n;,]', ' ', val_str)
    tokens = val_str.split()
    valid_docs = []
    for token in tokens:
        token_clean = token.replace('CTE', '').replace('CRT', '')
        if not token_clean: continue
        if token_clean.isdigit():
            valid_docs.append(token_clean)
            continue
        if re.match(r'^[A-Z]+\d+', token_clean):
            valid_docs.append(token_clean)
            continue
    return valid_docs

def _extract_documents_with_values(file):
    filename = file.filename.lower()
    # Dicionário agora armazena: {'SUM': valor_total, 'COUNT': qtd_aparicoes}
    docs_data = {} 
    read_log = []

    try:
        if filename.endswith(('.xls', '.xlsx')):
            sheets_dict = pd.read_excel(file, sheet_name=None, dtype=str) 
        else:
            try:
                df = pd.read_csv(file, sep=';', encoding='latin1', on_bad_lines='skip', dtype=str)
            except:
                file.seek(0)
                df = pd.read_csv(file, sep=',', encoding='utf-8', on_bad_lines='skip', dtype=str)
            sheets_dict = {'CSV': df}
        
        for sheet_name, df in sheets_dict.items():
            if df.empty: continue
            df.columns = [str(c).strip().upper() for c in df.columns]

            doc_col = None
            possible_names = ['CRT', 'CTE', 'CT-E', 'CRTS/CTES', 'CONHECIMENTO', 'DOC', 'MIC']
            for name in possible_names:
                if name in df.columns: doc_col = name; break
            
            if not doc_col:
                for col in df.columns:
                    if any(x in col for x in possible_names):
                        if 'DATA' not in col and 'VALOR' not in col and 'DT' not in col:
                            doc_col = col; break
            
            if not doc_col: continue 

            df = df.dropna(subset=[doc_col])
            df = df[df[doc_col].astype(str).str.strip() != '']
            df = df[df[doc_col].astype(str).str.lower() != 'nan']

            val_col = None
            possible_vals = ['VALOR', 'VLR', 'COST', 'TOTAL', 'RATEIO', 'VALOR FRETE']
            for v_name in possible_vals:
                if v_name in df.columns: val_col = v_name; break
            if not val_col:
                for col in df.columns:
                    if 'VALOR' in col and 'MERCADORIA' not in col: val_col = col; break

            items_in_sheet = 0
            for index, row in df.iterrows():
                raw_cell_val = row[doc_col]
                found_docs = _clean_cell_value(raw_cell_val)
                
                line_value = 0.0
                if val_col:
                    line_value = _parse_float_safe(row[val_col])

                if found_docs:
                    # Pega apenas o primeiro documento da célula
                    first_doc = found_docs[0]
                    items_in_sheet += 1
                    
                    # --- NOVA LÓGICA: SOMA VALOR E CONTA OCORRÊNCIAS ---
                    if first_doc not in docs_data:
                        docs_data[first_doc] = {'sum': 0.0, 'count': 0}
                    
                    docs_data[first_doc]['sum'] += line_value
                    docs_data[first_doc]['count'] += 1
            
            read_log.append(f"{sheet_name}: {items_in_sheet} docs")
                        
    except Exception as e:
        raise ValueError(f"Erro ao processar arquivo: {e}")
        
    return docs_data, read_log

@app.route('/upload', methods=['POST'])
def upload():
    raw_cnpj = request.form.get('cnpj')
    cnpj = re.sub(r"\D", "", raw_cnpj) if raw_cnpj else None
    numero = request.form.get('numero')
    tipocusto = request.form.get('tipocusto')
    valor_padrao_float = _parse_float_safe(request.form.get('valor_padrao', '0'))

    file = request.files.get('file')
    if not file: return redirect(url_for('index'))

    try:
        # docs_dict agora é: { 'DOC': {'sum': 10.0, 'count': 2} }
        docs_dict, read_log = _extract_documents_with_values(file)
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
            # Se a soma encontrada no arquivo for > 0, usa a soma.
            # Se a soma for 0, multiplica a quantidade de vezes que apareceu pelo valor padrão.
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
        valor = _parse_float_safe(val_str)
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