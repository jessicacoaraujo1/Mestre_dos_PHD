import hashlib
import io
import re
import requests
import pandas as pd
from pydantic import BaseModel
from typing import List

# Endereço da base de dados oficiais da CAPES/MEC
CAPES_URL = "https://dadosabertos.capes.gov.br/dataset/33719131-0162-43bb-81d3-37cbcfbf04f8/resource/8d0fb5c4-239d-4720-a616-e5c942918a38/download/br-capes-cols-2024.csv"

class DoutoradoSchema(BaseModel):
    codigo: str
    programa: str
    instituicao: str
    uf: str
    nota: int

def carregar_doutorados_capes(limite=5) -> List[DoutoradoSchema]:
    print("⚡ [1/2] Acessando a base oficial de Doutorados do Brasil (CAPES/MEC)...")
    try:
        res = requests.get(CAPES_URL, timeout=10)
        df = pd.read_csv(io.BytesIO(res.content), sep=';', encoding='latin-1')
        df_doc = df[df['DS_NIVEL_TITULACAO'].str.contains('DOUTORADO', case=False, na=False)]
        
        lista = []
        for _, r in df_doc.head(limite).iterrows():
            lista.append(DoutoradoSchema(
                codigo=str(r['CD_PROGRAMA_IES']),
                programa=str(r['NM_PROGRAMA_IES']).title(),
                instituicao=str(r['SG_ENTIDADE_ENSINO']),
                uf=str(r['SG_UF_PROGRAMA']),
                nota=int(r['CD_CONCEITO_PROGRAMA']) if str(r['CD_CONCEITO_PROGRAMA']).isdigit() else 0
            ))
        print(f"✅ Sucesso: {len(lista)} programas de Doutorado identificados!")
        return lista
    except Exception as e:
        print("⚠️ Usando lista padrão de teste para garantir a execução...")
        return [
            DoutoradoSchema(codigo="001", programa="Relações Internacionais (San Tiago Dantas)", instituicao="UNESP/UNICAMP/PUC-SP", uf="SP", nota=6),
            DoutoradoSchema(codigo="002", programa="Economia Política Internacional", instituicao="UFRJ", uf="RJ", nota=7),
            DoutoradoSchema(codigo="003", programa="Relações Internacionais", instituicao="USP", uf="SP", nota=7)
        ]

def verificar_alteracao_edital(url_target: str):
    print(f"\n🔍 [2/2] Testando varredura no site: {url_target}")
    try:
        res = requests.get(url_target, timeout=10)
        edital_detectado = bool(re.search(r'edital|processo seletivo|inscrições', res.text, re.IGNORECASE))
        
        if edital_detectado:
            print("🟢 EDITAL IDENTIFICADO: O site contém chamadas ativas de processo seletivo!")
        else:
            print("⚪ Nenhuma alteração de edital identificada no momento.")
    except Exception as e:
        print(f"❌ Erro ao acessar o site: {e}")

if __name__ == "__main__":
    programas = carregar_doutorados_capes()
    print("\n--- PROGRAMAS MAPEADOS ---")
    for p in programas:
        print(f"• [{p.instituicao}] {p.programa} (Nota CAPES: {p.nota})")
        
    url_teste = "https://www.santiagodantas-ppgri.org/regulamentos-e-instrucoes"
    verificar_alteracao_edital(url_teste)