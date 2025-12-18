# Rateio Importer - Sistema de Importação de Custos de Frete

Aplicação web desenvolvida em Python/Flask para automatizar o rateio de custos de Notas Fiscais de Entrada, vinculando-as a CRTs (Conhecimentos de Transporte) listados em planilhas Excel/CSV.

## 🚀 Funcionalidades

1.  **Busca de Nota Fiscal**: Localiza a nota de entrada pelo CNPJ do fornecedor e Número da Nota.
2.  **Leitura Inteligente de Arquivos**:
    *   Suporte a Excel (`.xlsx`, `.xls`) e CSV.
    *   Varredura automática em **todas as abas** do arquivo Excel.
    *   Identificação automática da coluna de **CRT** (busca por nomes similares).
    *   **Limpeza de Dados**: Utiliza Regex para remover prefixos numéricos de CRTs (ex: `079AR123` vira `AR123`).
3.  **Validação de Dados**: Confere se os CRTs da planilha existem no banco de dados antes da importação.
4.  **Interface de Conferência**: Permite visualizar quais CRTs foram encontrados e ajustar os valores de custo individualmente.
5.  **Gravação Segura**: Insere os dados na tabela `notafiscalentrada_rateiodocumento` respeitando a integridade do banco e formatação de moeda (BRL/USD).

## 🛠️ Tecnologias Utilizadas

*   **Backend**: Python 3, Flask.
*   **Banco de Dados**: PostgreSQL (biblioteca `psycopg2`).
*   **Processamento de Dados**: Pandas, OpenPyXL.
*   **Frontend**: HTML5, Bootstrap 5.

## ⚙️ Instalação e Configuração

### 1. Clone o repositório
```bash
git clone https://seu-repositorio.git
cd rateio-importer