
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
