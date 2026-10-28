# Mestre_dos_PHD

Sistema de monitoramento acadêmico e geração de apostilas para processos seletivos de pós-graduação.

## Visão geral

O projeto combina:

- Backend em Python com FastAPI
- Frontend em Next.js
- Banco SQLite para monitoramento de URLs
- Geração de PDF protegida com marca d'água e rastreabilidade por nome/CPF
- Notificações por Telegram e envio opcional de e-mail com PDF em anexo

## Stack

- Python 3.15+
- FastAPI
- ReportLab
- PyPDF
- Pandas
- Next.js 16
- React 19

## Estrutura do projeto

- `robo_api.py` — API principal com endpoints, monitoramento, e geração de apostilas
- `requirements.txt` — dependências do backend
- `painel/` — frontend em Next.js
- `editalhub.db` — banco SQLite local (gerado automaticamente)

## Pré-requisitos

- Python 3.15 ou superior
- Node.js 20+ e npm
- Git

## Instalação

### 1) Backend

```bash
cd /Users/jessicaaraujo/Desktop/edital-hub
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

### 2) Frontend

```bash
cd /Users/jessicaaraujo/Desktop/edital-hub/painel
npm install
```

## Variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto, se necessário, com configurações opcionais:

```env
TELEGRAM_TOKEN=seu_token
TELEGRAM_CHAT_ID=seu_chat_id
DB_FILE=editalhub.db
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASSWORD=sua_senha_ou_app_password
```

Observação: SMTP é opcional. Se não estiver configurado, o envio por e-mail simplesmente será ignorado.

## Execução

### Backend

```bash
cd /Users/jessicaaraujo/Desktop/edital-hub
. .venv/bin/activate
python robo_api.py
```

API disponível em:

- http://127.0.0.1:8000

### Frontend

```bash
cd /Users/jessicaaraujo/Desktop/edital-hub/painel
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Painel disponível em:

- http://127.0.0.1:3000

## Endpoints principais

- `GET /` — status da API
- `GET /api/programas` — lista de programas de pós-graduação
- `GET /api/verificar-edital` — consulta de edital em uma URL
- `GET /api/sistema/urls` — URLs monitoradas
- `POST /api/sistema/urls` — cadastrar portal para monitorar
- `DELETE /api/sistema/urls/{url_id}` — remover monitoramento
- `POST /api/apostila/gerar` — gerar PDF da apostila protegida

## Teste rápido de geração de PDF

```bash
curl -X POST http://127.0.0.1:8000/api/apostila/gerar \
  -H "Content-Type: application/json" \
  -d '{
    "nome_completo": "Maria Teste",
    "cpf": "123.456.789-09",
    "email": "teste@example.com",
    "nome_concurso": "Doutorado em Economia e Desenvolvimento - UFPA 2026",
    "modulos": [{
      "titulo": "Módulo I",
      "resumo": "Resumo de estudo",
      "topicos": [{"nome": "Tema 1", "prioridade": "Alta"}]
    }]
  }'
```

## Publicação no GitHub

Siga o fluxo de publicação do repositório remoto:

```bash
git add .
git commit -m "Atualiza sistema e PDF generator"
git push origin main
```

## Observações

- As credenciais de Telegram e SMTP devem ser configuradas em variáveis de ambiente ou arquivo `.env`.
- O banco SQLite e os arquivos temporários de PDF são gerados localmente durante a execução.
- O sistema foi validado localmente para start da API, do frontend e geração de apostila.
