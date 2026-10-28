import hashlib
import io
import os
import re
import sqlite3
import tempfile
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from functools import lru_cache
from typing import List, Optional

import pandas as pd
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
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
    "DIREITO",
    "CIÊNCIA POLÍTICA",
    "RELAÇÕES INTERNACIONAIS",
    "SOCIOLOGIA",
    "ADMINISTRAÇÃO",
    "ADMINISTRAÇÃO PÚBLICA",
    "PLANEJAMENTO URBANO E REGIONAL / DEMOGRAFIA",
    "CIÊNCIAS AMBIENTAIS",
    "MEIO AMBIENTE E SUSTENTABILIDADE",
    "FILOSOFIA",
    "GEOGRAFIA",
    "SERVIÇO SOCIAL",
    "INTERDISCIPLINAR",
]

DEFAULT_PROGRAMAS = [
    {
        "id": "ufpa-doutorado-2026",
        "instituicao": "Universidade Federal do Pará",
        "sigla_ies": "UFPA",
        "programa": "Programa de Pós-Graduação em Economia e Desenvolvimento",
        "uf": "PA",
        "area": "Economia",
        "nivel": "Doutorado",
        "nota_capes": "5",
        "status_juridico": "Pública",
        "previsao_edital": "Inscrições abertas",
    },
    {
        "id": "usp-mestrado-2027",
        "instituicao": "Universidade de São Paulo",
        "sigla_ies": "USP",
        "programa": "Mestrado em Economia",
        "uf": "SP",
        "area": "Economia",
        "nivel": "Mestrado",
        "nota_capes": "5",
        "status_juridico": "Pública",
        "previsao_edital": "Previsto 2027.1",
    },
    {
        "id": "puc-rio-ppg-direito",
        "instituicao": "Pontifícia Universidade Católica do Rio de Janeiro",
        "sigla_ies": "PUC-Rio",
        "programa": "Mestrado em Direito",
        "uf": "RJ",
        "area": "Direito",
        "nivel": "Mestrado",
        "nota_capes": "4",
        "status_juridico": "Privada",
        "previsao_edital": "Previsto 2026.2",
    },
    {
        "id": "unifesp-saude-publica",
        "instituicao": "Universidade Federal de São Paulo",
        "sigla_ies": "UNIFESP",
        "programa": "Doutorado em Saúde Pública",
        "uf": "SP",
        "area": "Saúde Pública",
        "nivel": "Doutorado",
        "nota_capes": "5",
        "status_juridico": "Pública",
        "previsao_edital": "Acompanhando",
    },
]


class ProgramaPosGraduacao(BaseModel):
    id: str
    instituicao: str
    sigla_ies: str
    programa: str
    uf: str
    area: str
    nivel: str
    nota_capes: str
    status_juridico: str
    previsao_edital: str


class NovaUrlReq(BaseModel):
    url: str
    nome_portal: str = "Portal acadêmico"


class TopicoEstudo(BaseModel):
    nome: str
    prioridade: str = "Alta"


class ModuloEstudo(BaseModel):
    titulo: str
    resumo: str
    topicos: List[TopicoEstudo] = []


class RequisicaoApostila(BaseModel):
    nome_completo: str = Field(..., min_length=2)
    cpf: str = Field(..., min_length=11)
    nome_concurso: str = Field(..., min_length=4)
    modulos: List[ModuloEstudo]


class AuthUser(BaseModel):
    name: Optional[str] = None
    email: str
    password: str


class AuthLogin(BaseModel):
    email: str
    password: str


class PaymentRequest(BaseModel):
    plan: str
    amount: float
    email: str
    cardName: Optional[str] = None
    cardNumber: Optional[str] = None
    expiry: Optional[str] = None
    cvv: Optional[str] = None
    cpf: Optional[str] = None


def init_db() -> None:
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS monitoramento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            nome_portal TEXT,
            ultimo_hash TEXT,
            ultima_verificacao TEXT,
            status_edital TEXT DEFAULT 'Acompanhando'
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


init_db()


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
        total_pages = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self.draw_security_layers(total_pages)
            super().showPage()
        super().save()

    def draw_security_layers(self, total_pages):
        self.saveState()
        self.setFont("Helvetica-Bold", 38)
        self.setFillColor(colors.HexColor("#CBD5E1"), alpha=0.22)
        self.translate(300, 400)
        self.rotate(45)
        self.drawCentredString(0, 0, "MONITORIA DE EDITAIS")
        self.restoreState()

        self.saveState()
        self.setFont("Helvetica", 7)
        self.setFillColor(colors.HexColor("#64748B"))
        info = f"ESTUDANTE: {self.user_name.upper()} | CPF: {self.user_cpf} | DOCUMENTO PROTEGIDO"
        self.drawCentredString(300, 775, info)
        self.drawCentredString(300, 15, f"{info} — Página {self._pageNumber} de {total_pages}")

        self.saveState()
        self.translate(15, 400)
        self.rotate(90)
        self.drawCentredString(0, 0, info)
        self.restoreState()

        self.saveState()
        self.translate(597, 400)
        self.rotate(-90)
        self.drawCentredString(0, 0, info)
        self.restoreState()
        self.restoreState()


def verificar_url(url: str) -> dict:
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        body = response.text.lower()
        padrao = r"edital|processo seletivo|inscrições abertas|seleção|mestrado|doutorado"
        detectado = bool(re.search(padrao, body, re.IGNORECASE))
        return {
            "status": "Alerta" if detectado else "Sem sinal",
            "mensagem": "Indícios de edital detectados." if detectado else "Nenhum indicativo forte de edital foi localizado.",
        }
    except Exception as exc:
        return {"status": "Erro", "mensagem": str(exc)}


def enviar_alerta_telegram(mensagem: str) -> bool:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as exc:
        print(f"[ERRO TELEGRAM] {exc}")
        return False


def executar_varredura_periodica() -> None:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, url, ultimo_hash FROM monitoramento")
    registros = cursor.fetchall()
    conn.close()

    for item_id, url, hash_anterior in registros:
        resultado = verificar_url(url)
        novo_hash = hashlib.md5(requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"}).text.encode("utf-8")).hexdigest() if requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"}).status_code == 200 else hash_anterior
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(DB_FILE)
        conn.execute(
            "UPDATE monitoramento SET ultimo_hash = ?, ultima_verificacao = ?, status_edital = ? WHERE id = ?",
            (novo_hash, now, "Alerta" if resultado["status"] == "Alerta" else "Acompanhando", item_id),
        )
        conn.commit()
        conn.close()

        if resultado["status"] == "Alerta":
            enviar_alerta_telegram(f"🚨 *ALERTA DE EDITAL*\n\n📍 {url}\n\n{resultado['mensagem']}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(executar_varredura_periodica, "interval", hours=6)
    scheduler.start()
    print("🚀 Agendador de varredura ativado a cada 6 horas.")
    yield
    scheduler.shutdown()


app = FastAPI(
    title="EditalHub Monitor",
    description="Sistema de monitoramento, rastreamento e estudo para programas de pós-graduação.",
    version="4.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def carregar_base_capes() -> Optional[pd.DataFrame]:
    try:
        response = requests.get(CAPES_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=25)
        response.raise_for_status()
        df = pd.read_csv(io.BytesIO(response.content), sep=';', encoding='latin-1', low_memory=False)
        return df.fillna("")
    except Exception as exc:
        print(f"[ERRO CAPES] {exc}")
        return None


@app.get("/")
def root():
    return {
        "status": "online",
        "title": "EditalHub Monitor",
        "description": "Sistema integrado para rastrear editais e produzir material de estudo.",
    }


@app.get("/api/overview")
def overview():
    return {
        "total": len(DEFAULT_PROGRAMAS),
        "abertos": 2,
        "em_breve": 2,
        "monitorados": 0,
    }


@app.get("/api/programas", response_model=List[ProgramaPosGraduacao])
def listar_programas(
    uf: Optional[str] = Query(None),
    nivel: Optional[str] = Query(None),
    busca: Optional[str] = Query(None),
    limite: int = Query(60, ge=1, le=200),
):
    df = carregar_base_capes()
    if df is None or df.empty:
        return [ProgramaPosGraduacao(**item) for item in DEFAULT_PROGRAMAS]

    areas = "|".join(re.escape(a) for a in AREAS_FOCO)
    mask = df["NM_AREA_CONHECIMENTO"].fillna("").str.upper().str.contains(areas, regex=True, na=False)

    if uf:
        mask &= df["SG_UF_PROGRAMA"].fillna("").str.upper() == uf.upper()
    if nivel:
        nivel_norm = nivel.upper()
        if nivel_norm != "TODOS":
            mask &= df["DS_NIVEL_TITULACAO"].fillna("").str.upper().str.contains(nivel_norm, na=False)
    if busca:
        termo = busca.upper()
        mask &= (
            df["NM_PROGRAMA_IES"].fillna("").str.upper().str.contains(termo, na=False)
            | df["SG_ENTIDADE_ENSINO"].fillna("").str.upper().str.contains(termo, na=False)
        )

    resultados = []
    for _, row in df[mask].head(limite).iterrows():
        nivel_value = str(row.get("DS_NIVEL_TITULACAO", "")).strip() or "Mestrado"
        resultados.append(
            ProgramaPosGraduacao(
                id=str(len(resultados)),
                instituicao=str(row.get("NM_ENTIDADE_ENSINO", "")).strip() or "Instituição",
                sigla_ies=str(row.get("SG_ENTIDADE_ENSINO", "")).strip() or "SIGLA",
                programa=str(row.get("NM_PROGRAMA_IES", "")).strip() or "Programa",
                uf=str(row.get("SG_UF_PROGRAMA", "")).strip() or "SP",
                area=str(row.get("NM_AREA_CONHECIMENTO", "")).strip() or "Área",
                nivel=nivel_value.title(),
                nota_capes=str(row.get("CD_CONCEITO_PROGRAMA", "5")).strip() or "5",
                status_juridico="Pública" if "UF" in str(row.get("SG_ENTIDADE_ENSINO", "")).upper() else "Privada",
                previsao_edital="Inscrições em andamento" if len(resultados) % 2 == 0 else "Previsto 2026.2",
            )
        )

    if not resultados:
        return [ProgramaPosGraduacao(**item) for item in DEFAULT_PROGRAMAS]
    return resultados


@app.get("/api/sistema/urls")
def listar_urls_monitoradas():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, url, nome_portal, ultima_verificacao, status_edital FROM monitoramento ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return {"urls": [dict(r) for r in rows]}


@app.post("/api/sistema/urls")
def cadastrar_url(req: NovaUrlReq):
    url = req.url.strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL inválida. Use http:// ou https://.")

    conn = sqlite3.connect(DB_FILE)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO monitoramento (url, nome_portal, ultimo_hash, ultima_verificacao, status_edital) VALUES (?, ?, ?, ?, ?)",
            (url, req.nome_portal, None, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Acompanhando"),
        )
        conn.commit()
        novo_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Esta URL já está cadastrada.")
    finally:
        conn.close()

    return {"sucesso": True, "id": novo_id, "url": url}


@app.delete("/api/sistema/urls/{url_id}")
def remover_url(url_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM monitoramento WHERE id = ?", (url_id,))
    conn.commit()
    conn.close()
    return {"sucesso": True}


@app.post("/api/sistema/urls/check")
def checar_url(req: NovaUrlReq):
    resultado = verificar_url(req.url)
    return {"status": resultado["status"], "mensagem": resultado["mensagem"]}


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
        textColor=colors.HexColor("#0F172A"),
        alignment=1,
        spaceAfter=15,
    )
    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        alignment=1,
        spaceAfter=18,
    )
    section_style = ParagraphStyle(
        "SectionStyle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=16,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=8,
    )

    story = []
    story.append(Paragraph("MONITORIA DE EDITAIS", title_style))
    story.append(Paragraph(f"<b>Plano de estudos personalizado</b><br/>{nome_concurso}", subtitle_style))
    story.append(Paragraph(f"Estudante: {usuario_nome}<br/>CPF: {usuario_cpf}", body_style))
    story.append(Spacer(1, 8))

    for mod in modulos:
        story.append(Paragraph(f"📌 {mod.titulo}", section_style))
        story.append(Paragraph(mod.resumo, body_style))
        if mod.topicos:
            data = [["Tema", "Prioridade", "Status"]]
            for topico in mod.topicos:
                data.append([topico.nome, topico.prioridade, "Pendente"])
            table = Table(data, colWidths=[260, 120, 110])
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
            story.append(Spacer(1, 8))

    def make_canvas(*args, **kwargs):
        return SecurityCanvas(*args, user_name=usuario_nome, user_cpf=usuario_cpf, **kwargs)

    doc.build(story, canvasmaker=make_canvas)
    print(f"✅ PDF gerado em {filepath}")


@app.post("/api/auth/register")
def register_user(payload: AuthUser):
    if not payload.email or not payload.password:
        raise HTTPException(status_code=400, detail="Email e senha são obrigatórios.")
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Senha deve ter pelo menos 6 caracteres.")

    conn = sqlite3.connect(DB_FILE)
    try:
        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (payload.name or payload.email.split('@')[0], payload.email.strip().lower(), hash_password(payload.password)),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Este e-mail já está cadastrado.")
    finally:
        conn.close()

    return {
        "status": "ok",
        "name": payload.name or payload.email.split('@')[0],
        "email": payload.email.strip().lower(),
    }


@app.post("/api/auth/login")
def login_user(payload: AuthLogin):
    conn = sqlite3.connect(DB_FILE)
    row = conn.execute(
        "SELECT name, email FROM users WHERE email = ? AND password_hash = ?",
        (payload.email.strip().lower(), hash_password(payload.password)),
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="Credenciais inválidas.")

    return {"status": "ok", "name": row[0], "email": row[1]}


@app.post("/api/payments/checkout")
def create_checkout(payload: PaymentRequest):
    if not payload.plan or payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Dados de pagamento inválidos.")
    if payload.cardNumber and len(str(payload.cardNumber).replace(" ", "")) < 12:
        raise HTTPException(status_code=400, detail="Número do cartão inválido.")

    return {
        "status": "approved",
        "plan": payload.plan,
        "amount": payload.amount,
        "email": payload.email,
        "provider": "simulado-local",
        "message": "Pagamento aprovado em ambiente de demonstração.",
    }


@app.post("/api/apostila/gerar")
def gerar_apostila(req: RequisicaoApostila, background_tasks: BackgroundTasks):
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, f"Apostila_{uuid.uuid4().hex[:8]}.pdf")

    gerar_apostila_pdf(
        filepath=filepath,
        nome_concurso=req.nome_concurso,
        modulos=req.modulos,
        usuario_nome=req.nome_completo,
        usuario_cpf=req.cpf,
    )

    background_tasks.add_task(lambda path: os.remove(path) if os.path.exists(path) else None, filepath)
    return FileResponse(
        path=filepath,
        filename=f"Apostila_{req.nome_completo.replace(' ', '_')}.pdf",
        media_type="application/pdf",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("robo_api:app", host="127.0.0.1", port=8000, reload=True)
