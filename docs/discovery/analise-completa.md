# Análise Completa — hora_calc (Somador de Horas)

> **Fases 2 + 3: Analyze + Document** — Workflow `brownfield-discovery`
> **Data:** 2026-07-19
> **Agentes:** aiox-architect + tactical-ddd + codenavi → aiox-master

---

## Parte I — Análise do Modelo de Domínio (tactical DDD)

### 1. Diagnóstico de Anemia: `Meeting`

```
Classe: Meeting (app/domain/models.py)

Severidade: MODERADA (score: 6/10)
```

#### Sinais Detectados

| Sinal | Peso | Evidência |
|-------|------|-----------|
| Campos públicos (dataclass) | +2 | Todos os campos são públicos por definição do `@dataclass` |
| Validação duplicada no service layer | +2 | `register_meeting()` e `update_meeting()` validam `duration_minutes <= 0` — deveria estar no modelo |
| Guards ausentes | +1 | Sem validação de `name` vazio, sem validação de ranges de horário |
| Primitive obsession | +1 | `name` e `card` são strings sem Value Objects |

#### O que a classe JÁ faz bem

- ✅ Properties calculadas (`duration_minutes`, `duration_hours`, `duration_decimal`)
- ✅ Uso de `time` para horários (não string)
- ✅ `card` opcional com `None` como sentinela

#### O que falta

- ❌ Sem `__post_init__` para validar invariantes
- ❌ Validação de duração positiva deveria estar no construtor, não no use case
- ❌ `name` não tem validação de tamanho/conteúdo
- ❌ Sem métodos de domínio com linguagem ubíqua (ex: `meeting.reschedule(start, end)`)
- ❌ `date` como `datetime | None` é confuso — deveria ser `date | None`

### 2. Análise de Building Blocks

#### 2.1 `Meeting` → **Entity**

**Justificativa:** Uma reunião tem identidade (data + índice no CSV + nome), mas não tem um ID único explícito. Atualmente é tratada como Value Object (comparada por atributos). Deveria ser uma Entity com `meeting_id: UUID` ou identificador único.

#### 2.2 `TimeInterval` → **Value Object** (sugerido)

Deveria existir um VO `TimeInterval` para encapsular:
```python
@dataclass(frozen=True)
class TimeInterval:
    start: time
    end: time
    
    def __post_init__(self):
        if self.start >= self.end:
            raise ValueError("End time must be after start time")
    
    @property
    def duration_minutes(self) -> int:
        return (self.end.hour * 60 + self.end.minute) - \
               (self.start.hour * 60 + self.start.minute)
```

#### 2.3 `MeetingName` → **Value Object** (sugerido)

```python
@dataclass(frozen=True)
class MeetingName:
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Meeting name cannot be empty")
        if len(self.value) > 200:
            raise ValueError("Meeting name too long")
```

#### 2.4 `MeetingUseCases` → **Application Service**

Atualmente mistura orquestração de caso de uso com lógica de domínio. Deveria ser puramente um Application Service que coordena o domínio.

---

## Parte II — Análise Arquitetural

### 3. Clean Architecture Compliance

| Camada | O que diz | Status | Observação |
|--------|-----------|--------|------------|
| **Domain** | Entidades e regras de negócio | ⚠️ | Meeting é anêmico, regras vazaram pro use case |
| **Use Cases** | Lógica de aplicação | ⚠️ | Mistura orquestração com validação de domínio |
| **Infrastructure** | Persistência, serviços externos | ✅ | CSV repository bem isolado |
| **Interfaces** | Web, API, UI | ⚠️ | Template HTML com JS inline, lógica de apresentação misturada |

#### Problemas de Acoplamento

1. **Use Case conhece Infrastructure** → `MeetingUseCases` recebe `repository` sem interface/contrato
2. **Domain não tem repositório abstrato** → Sem `MeetingRepository` protocol/ABC
3. **Interfaces acopla a Use Cases diretamente** → `routes.py` importa `MeetingUseCases` diretamente

### 4. Análise de Fluxo de Dados

#### 4.1 Fluxo Principal (Registro)

```
POST /registrar
  → routes.register()
    → time.fromisoformat(inicio)          # Parsing na interface (OK)
    → time.fromisoformat(fim)             # Parsing na interface (OK)
    → uc.register_meeting(name, start, end, card)
      → Meeting(...)                      # Criação do objeto
      → if duration_minutes <= 0           # Validação no lugar errado ❌
      → repository.save(meeting)          # Persistência
```

#### 4.2 Limitações do Repositório CSV

- **Índice de linha como ID** — frágil se múltiplos usuários/sessões
- **Sem transações** — escrita direta sem atomicidade
- **Race condition** — dois registros simultâneos podem corromper
- **Sem migrações** — schema CSV evolui sem controle
- **Locking** — sem file locking para acesso concorrente

### 5. Segurança

| Risco | Severidade | Descrição |
|-------|-----------|-----------|
| Path traversal no CSV viewer | Média | `GET /csv-files/{filename}` — sem sanitização robusta de path |
| Injeção CSV | Baixa | Nomes com `;` podem quebrar o formato |
| Sem CORS config | Baixa | API sem middlewares de segurança |
| Sem rate limiting | Baixa | Sem proteção contra abuso de endpoints |
| Sem validação de input | Média | Campos de formulário sem sanitização |

### 6. Performance

| Aspecto | Observação |
|---------|------------|
| Leitura de CSV | Arquivo inteiro lido na memória a cada requisição |
| Cache | Nenhum — toda requisição lê o CSV do disco |
| Templates | Renderizados em toda requisição (sem cache) |
| Arquivos grandes | CSV com centenas de linhas é lido integralmente |

### 7. Testes

**Status:** ❌ NENHUM TESTE EXISTE

| Tipo | Qtd | Observação |
|------|-----|------------|
| Unitários | 0 | Sem `pytest`, sem `unittest` |
| Integração | 0 | Sem testes de API |
| E2E | 0 | Sem testes de browser |
| Coverage | 0 | Sem ferramenta configurada |

---

## Parte III — Análise de Qualidade de Código

### 8. Code Smells Identificados

#### 8.1 Código Duplicado

```python
# meeting_use_cases.py:21-22 e 57-58
if meeting.duration_minutes <= 0:
    raise ValueError("End time must be after start time")
```

Lógica de validação duplicada em `register_meeting()` e `update_meeting()`.

#### 8.2 Formatação de Duração Duplicada

```python
# meeting_use_cases.py:35-41
# routes.py:23-30 (function _format_minutes)
# index.html: inline JS calcula novamente
```

O mesmo algoritmo de formatação `horas + minutos` aparece em 3+ lugares.

#### 8.3 Magic Numbers

```python
# meeting_use_cases.py:74
balance_minutes = 480 - total_minutes  # 480 = 8h * 60min
```

480 é hardcoded — deveria ser uma constante com nome (`DAILY_TARGET_MINUTES = 480`).

#### 8.4 Type Hints Insuficientes

```python
# meeting_use_cases.py:7
def __init__(self, repository):  # repository sem tipo!
```

### 9. CSS Analysis

**Arquivo:** `static/style.css` — 633 linhas, CSS puro, sem pré-processador

| Problema | Impacto |
|----------|---------|
| Sem metodologia de nomenclatura (BEM, etc.) | Dificulta manutenção |
| Sem variáveis CSS | Cores e valores repetidos |
| Sem responsividade para telas grandes | Containers têm max-width fixo |
| Animações via transições simples | Limitado |

### 10. Template Analysis

| Template | Linhas | JS | Problemas |
|----------|--------|----|-----------|
| `index.html` | 290 | Inline (195 linhas) | Lógica de negócio no frontend |
| `calculadora.html` | 381 | Inline (220 linhas) | Cálculos duplicados do backend |
| `csv-viewer.html` | 193 | Inline (125 linhas) | Sem tratamento de erro offline |

---

## Parte IV — Análise de Dados

### 11. Dados CSV Existentes

11 arquivos em `data/`: `Horas_03-07-2026.csv` a `Horas_17-07-2026.csv`

**Formato:**
```
Nome;Início;Fim;Duração;Horas;Card
Reunião XPTO;09:00;10:30;1h30min;1.50;PROJ-123
```

**Observações:**
- Campos `Duração` e `Horas` são calculados (reduntantes com Início/Fim)
- Sem validação de uniqueness de nome
- Card é inconsistente (alguns registros têm, outros não)
- Encoding UTF-8 (correto)
- Separador `;` — nomes com `;` quebram o parser

---

## Parte V — Resumo de Descobertas

### 12. Matriz de Débitos Técnicos

| ID | Débito | Categoria | Severidade | Esforço |
|----|--------|-----------|-----------|---------|
| D01 | Anemia do modelo Meeting | Domain | Alta | Médio |
| D02 | Zero testes | Quality | Crítica | Grande |
| D03 | Validação duplicada | Code Smell | Média | Pequeno |
| D04 | Índice como ID frágil | Infrastructure | Alta | Médio |
| D05 | Sem interface de repositório | Architecture | Média | Médio |
| D06 | Sem tratamento de erros consistente | Reliability | Alta | Médio |
| D07 | HTML/JS monolítico | Frontend | Média | Grande |
| D08 | CSS sem metodologia | Frontend | Baixa | Médio |
| D09 | 480 hardcoded | Code Smell | Baixa | Trivial |
| D10 | Sem configuração de ambiente | DevOps | Média | Pequeno |
| D11 | Path traversal no CSV viewer | Security | Alta | Médio |
| D12 | Sem logging | Observability | Média | Pequeno |
| D13 | Formatação de duração duplicada | Code Smell | Baixa | Pequeno |
| D14 | Sem cache de leitura CSV | Performance | Média | Médio |
| D15 | Dados calculados no CSV | Data | Baixa | Pequeno |

### 13. Métricas do Projeto

| Métrica | Valor |
|---------|-------|
| Arquivos Python | 6 |
| Linhas Python | 486 |
| Arquivos Frontend | 4 |
| Linhas Frontend | 1.497 |
| Total Arquivos App | 10 |
| Total Linhas App | 1.983 |
| Testes | 0 |
| Cobertura | 0% |
| Dependências | 4 |
| Endpoints | 11 |
| Arquivos CSV | 11 |
