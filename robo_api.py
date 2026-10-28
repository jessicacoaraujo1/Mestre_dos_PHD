import hashlib
import io
import os
import re
import smtplib
import sqlite3
import tempfile
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import lru_cache
from typing import List, Optional

import pandas as pd
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
DB_FILE = os.getenv("DB_FILE", "editalhub.db")
CAPES_URL = "https://dadosabertos.capes.gov.br/dataset/33719131-0162-43bb-81d3-37cbcfbf04f8/resource/8d0fb5c4-239d-4720-a616-e5c942918a38/download/br-capes-cols-2024.csv"

AREAS_FOCO = [
    "ECONOMIA",
    "ECONOMIA POLÍTICA",
    "DIREITO",
    "CIÊNCIA POLÍTICA E RELAÇÕES INTERNACIONAIS",
    "CIÊNCIA POLÍTICA",
    "SOCIOLOGIA",
    "ADMINISTRAÇÃO",
    "ADMINISTRAÇÃO PÚBLICA E DE EMPRESAS, CIÊNCIAS CONTÁBEIS E TURISMO",
    "PLANEJAMENTO URBANO E REGIONAL / DEMOGRAFIA",
    "CIÊNCIAS AMBIENTAIS",
    "MEIO AMBIENTE E SUSTENTABILIDADE",
    "BIODIVERSIDADE",
    "GEOGRAFIA",
    "ANTROPOLOGIA / ARQUEOLOGIA",
    "INTERDISCIPLINAR",
    "FILOSOFIA",
    "HISTÓRIA",
]


class ProgramaPosGraduacao(BaseModel):
    id: str
    instituicao_sigla: str
    instituicao_nome: str
    natureza_juridica: str
    programa_nome: str
    area_avaliacao: str
    nivel: str
    modalidade: str
    uf: str
    regiao: str
    nota_capes: int
    status: str
    previsao: str


class NovaUrlReq(BaseModel):
    url: str


class TopicoEstudo(BaseModel):
    nome: str
    prioridade: str = "Média"


class ModuloEstudo(BaseModel):
    titulo: str
    resumo: str
    topicos: List[TopicoEstudo] = []


class RequisicaoApostila(BaseModel):
    nome_completo: str = Field(..., json_schema_extra={"example": "Jéssica Caroline de Oliveira Araújo"})
    cpf: str = Field(..., json_schema_extra={"example": "123.456.789-00"})
    email: str = Field(..., json_schema_extra={"example": "usuario@email.com"})
    nome_concurso: str = Field(..., json_schema_extra={"example": "Doutorado em Economia e Desenvolvimento - UFPA 2026"})
    modulos: List[ModuloEstudo]


SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")


class SecurityCanvas(canvas.Canvas):
    def __init__(self, *args, user_name="", user_cpf="", **kwargs):
        super().__init__(*args, **kwargs)
        self.user_name = user_name
        self.user_cpf = user_cpf
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self.draw_security_layers(num_pages)
            super().showPage()
        super().save()

    def draw_security_layers(self, total_pages):
        self.saveState()
        self.setFont("Helvetica-Bold", 40)
        self.setFillColor(colors.HexColor("#CBD5E1"), alpha=0.22)
        self.translate(300, 400)
        self.rotate(45)
        self.drawCentredString(0, 0, "PROJETO GIGANTE")
        self.restoreState()

        self.saveState()
        self.setFont("Helvetica", 7)
        self.setFillColor(colors.HexColor("#64748B"))
        user_info = f"LICENCIADO PARA: {self.user_name.upper()} | CPF: {self.user_cpf} | DOCUMENTO PROTEGIDO"
        self.drawCentredString(300, 775, user_info)
        self.drawCentredString(300, 15, f"{user_info} — Página {self._pageNumber} de {total_pages}")

        self.saveState()
        self.translate(15, 400)
        self.rotate(90)
        self.drawCentredString(0, 0, user_info)
        self.restoreState()

        self.saveState()
        self.translate(597, 400)
        self.rotate(-90)
        self.drawCentredString(0, 0, user_info)
        self.restoreState()
        self.restoreState()


def remover_arquivo_temporario(filepath: str):
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as exc:
        print(f"Erro ao deletar arquivo temporário {filepath}: {exc}")


def obter_template_email_html(nome_usuario: str, nome_concurso: str, cpf_usuario: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sua Apostila Chegou!</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #0F172A; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout: fixed;">
            <tr>
                <td align="center" style="padding: 30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #1E293B; border-radius: 16px; overflow: hidden; border: 1px solid #334155;">
                        <tr>
                            <td align="center" style="padding: 40px 30px 20px 30px; background-color: #1E293B;">
                                <div style="display: inline-block; background-color: #2563EB; color: #FFFFFF; font-weight: bold; font-size: 16px; padding: 10px 18px; border-radius: 10px; letter-spacing: 1px;">
                                    PROJETO GIGANTE
                                </div>
                                <h1 style="color: #F8FAFC; font-size: 22px; margin-top: 20px; margin-bottom: 5px; font-weight: 700;">
                                    Sua Apostila Está Pronta! 📚
                                </h1>
                                <p style="color: #94A3B8; font-size: 14px; margin: 0;">
                                    Material direcionado de estudos e acompanhamento
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 20px 30px 30px 30px;">
                                <p style="color: #E2E8F0; font-size: 15px; line-height: 1.6; margin-bottom: 20px;">
                                    Olá, <strong style="color: #38BDF8;">{nome_usuario}</strong>!
                                </p>
                                <p style="color: #CBD5E1; font-size: 14px; line-height: 1.6; margin-bottom: 25px;">
                                    Sua apostila direcionada para o processo seletivo <strong style="color: #F8FAFC;">{nome_concurso}</strong> foi gerada com sucesso e já está anexada a este e-mail em formato PDF.
                                </p>
                                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #0F172A; border-radius: 12px; padding: 20px; border: 1px solid #334155; margin-bottom: 25px;">
                                    <tr>
                                        <td>
                                            <p style="color: #38BDF8; font-size: 13px; font-weight: bold; margin: 0 0 10px 0;">
                                                🔒 Rastreabilidade e Proteção
                                            </p>
                                            <p style="color: #94A3B8; font-size: 12px; line-height: 1.5; margin: 0;">
                                                Este documento é de uso pessoal e intransferível. Para sua segurança e proteção de direitos autorais, o PDF possui marca-d'água e marcação com seus dados nas margens:<br/>
                                                <strong style="color: #CBD5E1;">Titular:</strong> {nome_usuario}<br/>
                                                <strong style="color: #CBD5E1;">CPF Cadastrado:</strong> {cpf_usuario}
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                                <p style="color: #CBD5E1; font-size: 14px; line-height: 1.6; margin: 0;">
                                    Desejamos um excelente desempenho e uma jornada de estudos altamente produtiva!
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td align="center" style="padding: 20px 30px; background-color: #0F172A; border-top: 1px solid #334155;">
                                <p style="color: #64748B; font-size: 12px; margin: 0 0 5px 0;">
                                    © 2026 PROJETO GIGANTE — Sistema Automático de Gestão Acadêmica 24/7
                                </p>
                                <p style="color: #475569; font-size: 11px; margin: 0;">
                                    Este é um e-mail automático. Por favor, não responda a esta mensagem.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


def enviar_email_com_apostila(email_destino: str, nome_usuario: str, cpf_usuario: str, nome_concurso: str, filepath: str):
    try:
        if not SMTP_USER or not SMTP_PASSWORD:
            print("⚠️ SMTP não configurado; e-mail não foi enviado.")
            return

        msg = MIMEMultipart()
        msg["From"] = f"PROJETO GIGANTE <{SMTP_USER}>"
        msg["To"] = email_destino
        msg["Subject"] = f"📚 Sua Apostila Chegou: {nome_concurso}"

        html_corpo = obter_template_email_html(nome_usuario, nome_concurso, cpf_usuario)
        msg.attach(MIMEText(html_corpo, "html"))

        if os.path.exists(filepath):
            with open(filepath, "rb") as arquivo:
                anexo = MIMEApplication(arquivo.read(), _subtype="pdf")
                anexo.add_header("Content-Disposition", "attachment", filename=f"Apostila_PROJETO_GIGANTE_{nome_usuario.replace(' ', '_')}.pdf")
                msg.attach(anexo)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ E-mail HTML enviado com sucesso para {email_destino}!")
    except Exception as exc:
        print(f"❌ Erro no envio do e-mail estilizado: {exc}")


def gerar_apostila_pdf(filepath: str, nome_concurso: str, modulos: List[ModuloEstudo], usuario_nome: str, usuario_cpf: str):
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1E293B"),
        alignment=1,
        spaceAfter=15,
    )
    subtitle_style = ParagraphStyle(
        "SubTitleStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        alignment=1,
        spaceAfter=25,
    )
    section_style = ParagraphStyle(
        "SectionStyle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=15,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=10,
    )

    story = []
    story.append(Paragraph("PROJETO GIGANTE", title_style))
    story.append(Paragraph(f"<b>Apostila Direcionada de Estudos</b><br/>{nome_concurso}", subtitle_style))
    story.append(Spacer(1, 10))

    for modulo in modulos:
        story.append(Paragraph(f"📌 {modulo.titulo}", section_style))
        story.append(Paragraph(modulo.resumo, body_style))
        if modulo.topicos:
            data = [["Tópico do Edital", "Prioridade", "Status de Estudo"]]
            for topico in modulo.topicos:
                data.append([topico.nome, topico.prioridade, "[  ] Concluído"])

            table = Table(data, colWidths=[280, 100, 120])
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.append(table)
            story.append(Spacer(1, 15))

    def make_canvas(*args, **kwargs):
        return SecurityCanvas(*args, user_name=usuario_nome, user_cpf=usuario_cpf, **kwargs)

    doc.build(story, canvasmaker=make_canvas)
    print(f"✅ Apostila gerada com sucesso: {filepath}")


def garantir_banco() -> None:
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS monitoramento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            ultimo_hash TEXT,
            ultima_verificacao TEXT,
            status_edital TEXT DEFAULT 'Ativo'
        )
        """
    )
    conn.commit()
    conn.close()


def enviar_alerta_telegram(mensagem: str) -> bool:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as exc:
        print(f"Erro no envio via Telegram: {exc}")
        return False


@lru_cache(maxsize=1)
def carregar_base_capes() -> Optional[pd.DataFrame]:
    print("⏳ Baixando base completa da CAPES...")
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(CAPES_URL, headers=headers, timeout=30)
        response.raise_for_status()
        df = pd.read_csv(io.BytesIO(response.content), sep=';', encoding='latin-1', low_memory=False)
        df = df.fillna("")
        print(f"✅ Base carregada! Total de registros no Brasil: {len(df)}")
        return df
    except Exception as exc:
        print(f"❌ Erro ao carregar CAPES: {exc}")
        return None


def executar_varredura_periodica() -> None:
    print(f"\n⏰ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando varredura automática...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT url, ultimo_hash FROM monitoramento")
    paginas = cursor.fetchall()
    conn.close()

    if not paginas:
        print("ℹ️ Nenhuma URL cadastrada no banco para monitoramento.")
        return

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    for url_str, hash_anterior in paginas:
        try:
            resposta = requests.get(url_str, headers=headers, timeout=15)
            if resposta.status_code != 200:
                continue

            html_content = resposta.text
            hash_atual = hashlib.md5(html_content.encode("utf-8")).hexdigest()

            if hash_atual != (hash_anterior or ""):
                edital_detectado = bool(re.search(r"edital|processo seletivo|inscrições abertas|seleção", html_content, re.IGNORECASE))

                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE monitoramento SET ultimo_hash = ?, ultima_verificacao = ?, status_edital = ? WHERE url = ?",
                    (
                        hash_atual,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Alterado" if edital_detectado else "Sem alteração",
                        url_str,
                    ),
                )
                conn.commit()
                conn.close()

                if edital_detectado:
                    msg = (
                        f"🚨 *ALERTA AUTOMÁTICO DE NOVO EDITAL!*\n\n"
                        f"📍 *Portal:* `{url_str}`\n"
                        f"📅 *Detectado em:* {datetime.now().strftime('%d/%m/%Y às %H:%M')}\n\n"
                        f"🔗 [Acessar Portal]({url_str})"
                    )
                    enviar_alerta_telegram(msg)
                    print(f"✅ Alerta enviado no Telegram para: {url_str}")

        except Exception as exc:
            print(f"❌ Erro ao checar {url_str}: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    garantir_banco()
    scheduler = BackgroundScheduler()
    scheduler.add_job(executar_varredura_periodica, "interval", minutes=30)
    scheduler.start()
    print("🚀 Agendador em execução: varredura a cada 30 minutos.")
    yield
    scheduler.shutdown()
    print("🛑 Agendador desligado.")


app = FastAPI(
    title="EditalHub API Pro",
    description="Motor de busca avançado para pós-graduação e monitoramento acadêmico.",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "EditalHub API Pro Online", "telegram": "Configurado"}


@app.get("/api/programas", response_model=List[ProgramaPosGraduacao])
def listar_todos_programas(
    uf: Optional[str] = Query(None, description="Filtrar por UF (ex: PA, SP)"),
    busca: Optional[str] = Query(None, description="Buscar por palavra-chave no nome do programa"),
):
    df = carregar_base_capes()
    if df is None or df.empty:
        return []

    df = df.fillna("")
    padrao_areas = "|".join(re.escape(a) for a in AREAS_FOCO)
    mask_area = df.get("NM_AREA_CONHECIMENTO", pd.Series(["" for _ in range(len(df))])).astype(str).str.upper().str.contains(padrao_areas, regex=True, na=False)
    mask_nivel = df.get("DS_NIVEL_TITULACAO", pd.Series(["" for _ in range(len(df))])).astype(str).str.upper().str.contains(r"MESTRADO|DOUTORADO", regex=True, na=False)
    df_filtrado = df[mask_area & mask_nivel].copy()

    if uf:
        df_filtrado = df_filtrado[df_filtrado.get("SG_UF_PROGRAMA", "").astype(str).str.upper() == uf.upper()]

    if busca:
        termo = busca.upper()
        mask_busca = (
            df_filtrado.get("NM_PROGRAMA_IES", "").astype(str).str.upper().str.contains(termo, na=False)
            | df_filtrado.get("SG_ENTIDADE_ENSINO", "").astype(str).str.upper().str.contains(termo, na=False)
        )
        df_filtrado = df_filtrado[mask_busca]

    programas_retorno: List[ProgramaPosGraduacao] = []
    for idx, row in df_filtrado.iterrows():
        nivel_bruto = str(row.get("DS_NIVEL_TITULACAO", "")).upper()
        nivel_refinado = "Doutorado" if "DOUTORADO" in nivel_bruto else "Mestrado"
        modalidade = "Profissional" if "PROFISSIONAL" in nivel_bruto else "Acadêmico"
        natureza = str(row.get("CS_STATUS_JURIDICO", "Não informado")).title()

        nota_raw = str(row.get("CD_CONCEITO_PROGRAMA", "A"))
        nota_final = int(nota_raw) if nota_raw.isdigit() else 0

        programas_retorno.append(
            ProgramaPosGraduacao(
                id=str(idx),
                instituicao_sigla=str(row.get("SG_ENTIDADE_ENSINO", "")).strip(),
                instituicao_nome=str(row.get("NM_ENTIDADE_ENSINO", "")).title().strip(),
                natureza_juridica=natureza,
                programa_nome=str(row.get("NM_PROGRAMA_IES", "")).title().strip(),
                area_avaliacao=str(row.get("NM_AREA_CONHECIMENTO", "")).title().strip(),
                nivel=nivel_refinado,
                modalidade=modalidade,
                uf=str(row.get("SG_UF_PROGRAMA", "")).strip(),
                regiao=str(row.get("NM_REGIAO", "")).title().strip(),
                nota_capes=nota_final,
                status="Em Monitoramento",
                previsao="Aguardando Edital",
            )
        )

    return programas_retorno


@app.get("/api/verificar-edital")
def checar_edital(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resposta = requests.get(url, headers=headers, timeout=15)
        resposta.raise_for_status()
        padrao = r"edital.*202[6-9]|processo seletivo|inscrições abertas|seleção.*mestrado|seleção.*doutorado|chamada pública"
        edital_encontrado = bool(re.search(padrao, resposta.text, re.IGNORECASE))
        if edital_encontrado:
            msg = (
                f"🚨 *ALERTA DE EDITAL - EDITALHUB PRO!*\n\n"
                f"🔎 O robô detectou movimento de processo seletivo ou inscrições abertas!\n\n"
                f"📍 *Acesse a página:* [Clique aqui]({url})"
            )
            enviado = enviar_alerta_telegram(msg)
            return {
                "status": "Aberto",
                "alerta_enviado": enviado,
                "url": url,
                "mensagem": "Indícios de edital encontrados. Notificação enviada!",
            }
        return {
            "status": "Fechado",
            "alerta_enviado": False,
            "url": url,
            "mensagem": "Nenhum termo de seleção detectado no momento.",
        }
    except Exception as exc:
        return {"status": "Erro de Conexão", "url": url, "detalhe": str(exc)}


@app.get("/api/sistema/urls")
def listar_urls_monitoradas():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, url, ultimo_hash, ultima_verificacao, status_edital FROM monitoramento ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return {
        "total": len(rows),
        "urls_monitoradas": [
            {
                "id": r[0],
                "url": r[1],
                "hash_md5": r[2],
                "ultima_verificacao": r[3],
                "status_edital": r[4],
            }
            for r in rows
        ],
    }


@app.get("/api/sistema/dashboard-status")
def status_geral_sistema():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM monitoramento")
    total_urls = cursor.fetchone()[0]
    conn.close()
    return {
        "status_servidor": "Operacional 🟢",
        "agendador": "Ativo (APScheduler 30m) ⏰",
        "telegram_bot": "Configurado 📱" if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID else "Sem token configurado",
        "chat_id_destino": TELEGRAM_CHAT_ID,
        "total_sites_monitorados": total_urls,
        "banco_dados": f"SQLite ({DB_FILE}) 💾",
    }


@app.post("/api/sistema/urls")
def cadastrar_url_monitoramento(req: NovaUrlReq):
    url_limpa = req.url.strip()
    if not url_limpa.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="A URL precisa iniciar com http:// ou https://")

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO monitoramento (url, status_edital) VALUES (?, ?)",
            (url_limpa, "Ativo"),
        )
        conn.commit()
        novo_id = cursor.lastrowid
        conn.close()
        return {"sucesso": True, "mensagem": "Portal cadastrado com sucesso no monitoramento!", "id": novo_id, "url": url_limpa}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Esta URL já está cadastrada no sistema.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro interno no banco: {str(exc)}")


@app.post("/api/monitorar-pagina")
def monitorar_pagina(req: NovaUrlReq):
    return cadastrar_url_monitoramento(req)


@app.delete("/api/sistema/urls/{url_id}")
def remover_url_monitoramento(url_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM monitoramento WHERE id = ?", (url_id,))
    linhas_afetadas = cursor.rowcount
    conn.commit()
    conn.close()

    if linhas_afetadas == 0:
        raise HTTPException(status_code=404, detail="URL não encontrada no banco de dados.")

    return {"sucesso": True, "mensagem": f"Portal com ID {url_id} removido com sucesso!"}


@app.post("/api/apostila/gerar")
def gerar_apostila_endpoint(req: RequisicaoApostila, background_tasks: BackgroundTasks):
    try:
        temp_dir = tempfile.gettempdir()
        filename = f"Apostila_{uuid.uuid4().hex[:8]}.pdf"
        filepath = os.path.join(temp_dir, filename)

        gerar_apostila_pdf(
            filepath=filepath,
            nome_concurso=req.nome_concurso,
            modulos=req.modulos,
            usuario_nome=req.nome_completo,
            usuario_cpf=req.cpf,
        )

        background_tasks.add_task(enviar_email_com_apostila, req.email, req.nome_completo, req.cpf, req.nome_concurso, filepath)
        background_tasks.add_task(remover_arquivo_temporario, filepath)

        return FileResponse(
            path=filepath,
            filename=f"Apostila_ProjetoGigante_{req.nome_completo.replace(' ', '_')}.pdf",
            media_type="application/pdf",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar apostila PDF: {str(exc)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("robo_api:app", host="127.0.0.1", port=8000, reload=True, timeout_keep_alive=30)
