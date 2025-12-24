import re
import math
import pandas as pd
from typing import List, Dict, Tuple, Any

class ParseUtils:
    @staticmethod
    def parse_float_safe(val_str):
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

    @staticmethod
    def clean_cell_value(raw_val) -> List[str]:
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

class FileProcessor:
    @staticmethod
    def extract_documents_with_values(file) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
        filename = file.filename.lower()
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
                possible_names = ['CRT', 'CTE', 'CT-E', 'CRTS/CTES', 'CONHECIMENTO']
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
                    found_docs = ParseUtils.clean_cell_value(raw_cell_val)
                    
                    line_value = 0.0
                    if val_col:
                        line_value = ParseUtils.parse_float_safe(row[val_col])

                    if found_docs:
                  
                        first_doc = found_docs[0]
                        items_in_sheet += 1
                        
                        if first_doc not in docs_data:
                            docs_data[first_doc] = {'sum': 0.0, 'count': 0}
                        
                        docs_data[first_doc]['sum'] += line_value
                        docs_data[first_doc]['count'] += 1
                
                read_log.append(f"{sheet_name}: {items_in_sheet} docs")
                            
        except Exception as e:
            raise ValueError(f"Erro ao processar arquivo: {e}")
            
        return docs_data, read_log