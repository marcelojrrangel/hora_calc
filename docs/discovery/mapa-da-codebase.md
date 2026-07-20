# Mapa da Codebase — hora_calc (Somador de Horas)

> **Fase 1: Explore** — Workflow `brownfield-discovery`
> **Data:** 2026-07-19
> **Agente:** aiox-master + codenavi

---

## 1. Visão Geral

**App:** Somador de Horas — Rastreador de reuniões/tempo com saldo diário de 8h (480 min)
**Stack:** Python + FastAPI + Jinja2 + Uvicorn
**Porta:** 8000 (`http://127.0.0.1:8000`)
**Entrypoint:** `run.py` → `app.main:app`

### 1.1 Estrutura de Diretórios

```
hora_calc/
├── run.py                              # Entrypoint (uvicorn)
├── requirements.txt                    # 4 dependências
├── app/
│   ├── __init__.py                     # Vazio
│   ├── main.py                         # Factory FastAPI + DI manual
│   ├── domain/
│   │   └── models.py                   # Meeting dataclass
│   ├── use_cases/
│   │   └── meeting_use_cases.py        # Lógica de negócio (CRUD + saldo)
│   ├── infrastructure/
│   │   └── csv_repository.py           # Persistência CSV
│   └── interfaces/
│       └── web/
│           ├── routes.py               # 11 endpoints FastAPI
│           ├── templates/
│           │   ├── index.html          # Página principal (290 linhas, JS inline)
│           │   ├── calculadora.html    # Calculadora de horas (381 linhas, JS inline)
│           │   └── csv-viewer.html     # Visualizador CSV (193 linhas, JS inline)
│           └── static/
│               └── style.css           # CSS único (633 linhas)
├── data/                               # Dados CSV
│   └── Horas_DD-MM-YYYY.csv            # 11 arquivos (Julho/2026)
├── docs/                               # Documentação
│   ├── discovery/                      # (output deste workflow)
│   ├── codemin-arch.md                 # Doc de arquitetura de OUTRO projeto (CodeMin)
│   ├── codemin-prd.md
│   ├── codemin-qa-report.md
│   └── codemin-stories.md
├── .aiox-core/                         # Framework AIOX (orquestração multi-agente)
├── .opencode/                          # Integração OpenCode
└── opencode.json                       # Config OpenCode
```

---

## 2. Camadas Arquiteturais

### 2.1 Domain (`app/domain/models.py`)

**Classe:** `Meeting` (dataclass)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `name` | `str` | Nome da reunião |
| `start_time` | `time` | Horário de início |
| `end_time` | `time` | Horário de fim |
| `date` | `datetime \| None` | Data (opcional, default = None) |
| `card` | `str \| None` | Código do card (opcional) |

**Properties:**
- `duration_minutes` → `int` — Duração em minutos (end - start)
- `duration_hours` → `str` — Duração formatada (ex: "1h30min")
- `duration_decimal` → `Decimal` — Duração em horas decimais (ex: 1.50)

### 2.2 Use Cases (`app/use_cases/meeting_use_cases.py`)

**Classe:** `MeetingUseCases`

| Método | Descrição |
|--------|-----------|
| `register_meeting()` | Cria e persiste reunião (valida: end > start) |
| `get_today_meetings()` | Reuniões de hoje |
| `get_meetings_by_date()` | Reuniões por data |
| `get_total_hours()` | Total formatado (ex: "3h45min") |
| `get_meetings_with_index()` | Lista com índices para edição |
| `update_meeting()` | Atualiza reunião por índice |
| `delete_meeting()` | Remove reunião por índice |
| `get_total_decimal()` | Total em decimal (ex: "3.75") |
| `get_balance()` | Saldo do dia (480 min - total) |
| `list_csv_files()` | Lista arquivos CSV |
| `read_csv_file()` | Lê conteúdo de arquivo CSV |

### 2.3 Infrastructure (`app/infrastructure/csv_repository.py`)

**Classe:** `CsvMeetingRepository`

**Formato CSV:** `data/Horas_DD-MM-YYYY.csv`
- Separador: `;` (ponto e vírgula)
- Cabeçalho: `Nome;Início;Fim;Duração;Horas;Card`
- Codificação: UTF-8

**Métodos:** save, find_by_date, find_by_date_with_index, update_by_index, delete_by_index, exists, list_files, read_file

### 2.4 Interfaces/Web (`app/interfaces/web/routes.py`)

**Router FastAPI** com 11 endpoints:

| Rota | Método | Descrição |
|------|--------|-----------|
| `/` | GET | Página inicial (reuniões de hoje) |
| `/registrar` | POST | Registrar reunião |
| `/reunioes?data=` | GET | Listar reuniões (JSON) |
| `/reunioes/{index}` | PUT | Atualizar reunião |
| `/reunioes/{index}` | DELETE | Excluir reunião |
| `/calculadora` | GET | Calculadora de horas |
| `/resumo?data=` | GET | Resumo do dia |
| `/resumo/restante` | GET | Saldo restante hoje |
| `/csv-viewer` | GET | Visualizador CSV |
| `/csv-files` | GET | Listar arquivos CSV |
| `/csv-files/{filename}` | GET | Ler arquivo CSV |

---

## 3. Fluxo de Dados

```
Browser                          FastAPI Server
   │                                  │
   │  GET /                           │
   │─────────────────────────────────►│
   │                                  │──► routes.index()
   │                                  │    └──► MeetingUseCases.get_meetings_by_date(today)
   │                                  │         └──► CsvMeetingRepository.find_by_date()
   │                                  │              └──► data/Horas_DD-MM-YYYY.csv
   │                                  │
   │◄── HTML (Jinja2 template) ──────│
   │                                  │
   │  POST /registrar (FormData)      │
   │─────────────────────────────────►│
   │                                  │──► routes.register()
   │                                  │    └──► MeetingUseCases.register_meeting()
   │                                  │         └──► CsvMeetingRepository.save()
   │                                  │              └──► append to CSV
   │◄── JSON {success, meeting} ──────│
```

---

## 4. Dependências Externas

| Pacote | Versão | Uso |
|--------|--------|-----|
| fastapi | >=0.104.0 | Framework web |
| uvicorn | >=0.24.0 | Servidor ASGI |
| jinja2 | >=3.1.0 | Template engine |
| python-multipart | >=0.0.6 | Parsing de FormData |

**Nenhuma dependência de teste** (sem pytest, sem test files).

---

## 5. Dados Existentes

11 arquivos CSV em `data/` (Julho/2026):
- `Horas_03-07-2026.csv` a `Horas_17-07-2026.csv`
- Formato: `Nome;Início;Fim;Duração;Horas;Card`
- Separação por data (um arquivo por dia)

---

## 6. Observações da Exploração

### 6.1 Pontos Fortes
- ✅ Clean Architecture (separação Domain / Use Cases / Infrastructure / Interfaces)
- ✅ DI manual simples (construtor recebe repository)
- ✅ Jinja2 templates server-side com JS para interatividade
- ✅ Propriedades calculadas no model (duration_minutes, duration_hours, duration_decimal)
- ✅ Uso de `date` como domínio (não string)

### 6.2 Pontos de Atenção
- ⚠️ **Zero testes** — sem pytest, sem test runner configurado
- ⚠️ **Validação frágil** — apenas `end > start` é validado
- ⚠️ **Sem type hints em `_repository`** — `MeetingUseCases.__init__` recebe `repository` sem tipo
- ⚠️ **Tratamento de erros inconsistente** — ValueError vira HTTP 400, mas sem padronização
- ⚠️ **CSV como BD** — race conditions em escrita concorrente, sem transactions
- ⚠️ **Índice de linha como ID** — frágil para updates/deletes em concorrência
- ⚠️ **HTML/JS monolítico** — templates grandes (290-381 linhas) com JS inline misturado
- ⚠️ **CSS único** — 633 linhas em style.css, sem metodologia (BEM, CSS Modules)
- ⚠️ **Sem configuração de ambiente** — dev/prod não diferenciados
- ⚠️ **Sem logging** — sem tratamento de logs, erros silenciosos
- ⚠️ **Horário fixo 8h (480 min)** — hardcoded, não configurável

---

## 7. Arquivos por Camada (Linhas de Código)

| Camada | Arquivo | Linhas |
|--------|---------|--------|
| Entrypoint | `run.py` | 11 |
| Main/Factories | `app/main.py` | 23 |
| Domain | `app/domain/models.py` | 36 |
| Use Cases | `app/use_cases/meeting_use_cases.py` | 81 |
| Infrastructure | `app/infrastructure/csv_repository.py` | 149 |
| Interfaces | `app/interfaces/web/routes.py` | 186 |
| Template | `templates/index.html` | 290 |
| Template | `templates/calculadora.html` | 381 |
| Template | `templates/csv-viewer.html` | 193 |
| CSS | `static/style.css` | 633 |
| **Total Python** | 6 arquivos | **486** |
| **Total Frontend** | 4 arquivos | **1.497** |
| **Total Projeto** | 10 arquivos | **1.983** |
