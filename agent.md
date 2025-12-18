LP responsavel por importar rateio de nota fiscal, antes de importar o arquivo deve ser informado cnpj do cliente e o nr da nota fiscal, e o tipo de custo ( tipo de custo cadastrado em uma tablea separada conforme select abaixo, sistema deve permitir selecionar um dos tipos de custo ja cadastrados).
Apos informar os dados conforme acima, o sistema deve trazer as informaçoes da nota fiscal conforme select abaixo, para que o usuario confirme se esta trazendo a nota correta antes de importar o arquivo de rateio.
Apos conferencia, o usuario deve importar o arquivo de rateio, que sera vinculado a nota fiscal conforme cnpj/cpf e numero da nota informado..
Sistema entao deve abrir uma tela onde o usuario podera conferir e alterar o valor do rateio antes de gravar os dados no sistema.
Nesta ultima tela deve constar o numero da nota, cnpj/cpf, razao social, numero do CRT ( venda importação do arquivo), tipo de custo selecionado e o valor do custo( deve permitir alteração do valor)



Select para trazer as informaçoes da notas fiscais após informar cnpj/cpf e numero da nota:
"
SELECT DISTINCT
     notafiscalentrada.grupo
    ,notafiscalentrada.empresa
    ,notafiscalentrada.filial
    ,notafiscalentrada.unidade
    ,fnc_formata_cnpjcpfcod(notafiscalentrada.cnpjcpfcodigo) AS cnpjcpfcodigoformatado
    ,initcap(cadastro.razaosocial) AS razaosocial
    ,notafiscalentrada.cnpjcpfcodigo
    ,notafiscalentrada.serie
    ,notafiscalentrada.numero
    ,notafiscalentrada.dtemissao
    ,notafiscalentrada.dtentrada
    ,notafiscalentrada.valorprodutos
    ,notafiscalentrada.valorservicos
    ,notafiscalentrada.valortotalnotafiscal
    ,notafiscalentrada.chaveacessonfe
    ,notafiscalentrada.modelo
    ,notafiscalentrada.tipoinclusao
    ,notafiscalentrada.dtemissao::VARCHAR AS dataformatobanco
    ,notafiscalentrada.processo
    ,notafiscalentrada.dtinc 		
    ,fnc_formata_cnpjcpfcod(despesaoperacional.motorista) AS motoristaformatado
    ,initcap(cadastromotorista.razaosocial) AS razaosocialmotorista
    ,notafiscalentrada.usuarioemissor
    ,usuario.nomecompleto
    ,CASE 
        WHEN despesaoperacional.tipodocumento = 27 THEN coleta.dtemissao::DATE 
        WHEN despesaoperacional.tipodocumento = 201 THEN transporte.dtemissao::DATE
     END AS dtemissaocoleta		
    ,CASE 
        WHEN despesaoperacional.tipodocumento = 27 THEN coleta.numero 
        WHEN despesaoperacional.tipodocumento = 201 THEN transporte.numero
      END AS numerocoleta

FROM notafiscalentrada

-- Dados do Usuário Emissor
LEFT JOIN usuario 
    ON usuario.codigo = notafiscalentrada.usuarioemissor

-- Dados do Fornecedor da Nota
JOIN cadastro
    ON cadastro.codigo = notafiscalentrada.cnpjcpfcodigo

-- Ligação com Itens da Ordem de Compra (Causa da duplicação de linhas, tratada pelo DISTINCT)
LEFT JOIN notafiscalentrada_item_ordemcomprarecebida
    ON notafiscalentrada_item_ordemcomprarecebida.grupo = notafiscalentrada.grupo
    AND notafiscalentrada_item_ordemcomprarecebida.empresa = notafiscalentrada.empresa
    AND notafiscalentrada_item_ordemcomprarecebida.cnpjcpfcodigo = notafiscalentrada.cnpjcpfcodigo
    AND notafiscalentrada_item_ordemcomprarecebida.dtemissao = notafiscalentrada.dtemissao
    AND notafiscalentrada_item_ordemcomprarecebida.serie = notafiscalentrada.serie
    AND notafiscalentrada_item_ordemcomprarecebida.numero = notafiscalentrada.numero

-- Ligação com Despesa Operacional (Para pegar Motorista e vínculos de transporte)
LEFT JOIN despesaoperacional
    ON notafiscalentrada_item_ordemcomprarecebida.grupo = despesaoperacional.grupo
    AND notafiscalentrada_item_ordemcomprarecebida.empresa = despesaoperacional.empresa
    AND notafiscalentrada_item_ordemcomprarecebida.filialordemcompra = despesaoperacional.filialordemcompra
    AND notafiscalentrada_item_ordemcomprarecebida.unidadeordemcompra = despesaoperacional.unidadeordemcompra
    AND notafiscalentrada_item_ordemcomprarecebida.diferenciadornumeroordemcompra = despesaoperacional.diferenciadornumeroordemcompra
    AND notafiscalentrada_item_ordemcomprarecebida.numeroordemcompra = despesaoperacional.numeroordemcompra

-- Dados do Motorista
LEFT JOIN cadastro AS cadastromotorista
    ON cadastromotorista.codigo = despesaoperacional.motorista

-- Ligação com Coleta
LEFT JOIN coleta
    ON coleta.grupo = despesaoperacional.grupo
    AND coleta.empresa = despesaoperacional.empresa
    AND coleta.filial = despesaoperacional.filialdocumento
    AND coleta.unidade = despesaoperacional.unidadedocumento
    AND coleta.diferenciadornumero = despesaoperacional.diferenciadornumerodocumento
    AND coleta.serie = despesaoperacional.seriedocumento
    AND coleta.numero = despesaoperacional.numerodocumento
    AND despesaoperacional.tipodocumento = 27       		

-- Ligação com Transporte
LEFT JOIN transporte
    ON transporte.grupo = despesaoperacional.grupo
    AND transporte.empresa = despesaoperacional.empresa
    AND transporte.diferenciadornumero = despesaoperacional.diferenciadornumerodocumento
    AND transporte.numero = despesaoperacional.numerodocumento
    AND despesaoperacional.tipodocumento = 201

-- WHERE com Filtros Dinâmicos
WHERE  
    notafiscalentrada.grupo = 1
    AND notafiscalentrada.empresa = 1
    AND notafiscalentrada.numero = 42900
    and notafiscalentrada.cnpjcpfcodigo = '07473735018390'

ORDER BY
    notafiscalentrada.dtemissao DESC
   ,notafiscalentrada.dtentrada DESC
   ,notafiscalentrada.numero;

   "





   select para trazer os tipos de custo cadastrados para selecionar antes de importar o arquivo de rateio:
   "SELECT tipocusto.codigo,
       tipocusto.descricao
       
FROM tipocusto

LEFT JOIN grupocusto
     ON grupocusto.grupo = tipocusto.grupo
     AND grupocusto.empresa = tipocusto.empresa
     AND grupocusto.codigo = tipocusto.grupocusto

   
WHERE tipocusto.ativoinativo = '1';
   "



Insert para gravar o rateio no banco de dados:

"INSERT INTO notafiscalentrada_rateiodocumento 
 (grupo, 
 empresa, 
 cnpjcpfcodigo, 
 dtemissao, 
 serie, 
 numero, 
 sequencia, 
 dtinc,
 dtalt, 
 tipodocumento, 
 grupodocumento, 
 empresadocumento,
 filialdocumento, 
 unidadedocumento, 
 cnpjcpfcodigodocumento, 
 dtemissaodocumento,
 diferenciadornumerodocumento, 
 seriedocumento, 
 numerosequenciadocumento, 
 pesodocumento, 
 valor, 
 tipocusto)
 
values(
notafiscalentrada.grupo,
notafiscalentrada.empresa,
notafiscalentrada.cpfcnpjcodigo,
notafiscalentrada.dtemissao,
notafiscalentrada.serie,
notafiscalentrada.numero,
coalesce((select max(sequencia) from notafiscalentrada_rateiodocumento where grupo= notafiscalentrada.grupo and empresa=notafiscalentrada.empresa and cnpjcpfcodigo=notafiscalentrada.cpfcnpjcodigo and dtemissao=notafiscalentrada.dtemissao and serie=notafiscalentrada.serie and numero=notafiscalentrada.numero),1)+1,
now(),
null,
crt.tipodocumento
crt.grupo
crt.empresa,
crt.filial,
crt.unidade,
null,
crt.dtemissao,
crt.diferenciadorsequencia,
crt.sequencia,
crt.pesobruto, --arredondado
valor, 
tipocusto
)
"



select para trazer os dados do crt ( numero do CRT sera pego atravez da planilha de rateio importada)

"select crt.tipodocumento,
crt.grupo,
crt.empresa,
crt.filial,
crt.unidade,
crt.dtemissao,
crt.diferenciadorsequencia,
crt.sequencia,
crt.pesobruto

from crt where numero = 'UY184202555'
"