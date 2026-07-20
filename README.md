# Somador de Horas

Aplicacao web para registro e calculo de horas de reunioes. Permite registrar reunioes com inicio, fim e card associado, calculando automaticamente o total de horas e o saldo em relacao a meta diaria.

## Funcionalidades

- Registro de reunioes com nome, horario de inicio/fim e card
- Calculo automatico de duracao e total de horas
- Controle de saldo (meta diaria configuravel, padrao 8h)
- Visualizacao de dados em CSV
- Calculadora de horas independente
- Resumo diario com total em horas e decimal
- Autenticacao por senha

## Requisitos

- Python 3.11+
- pip

## Instalacao

```bash
git clone https://github.com/marcelojrrangel/hora_calc.git
cd hora_calc
pip install -r requirements.txt
```

## Configuracao

Copie o arquivo `.env.example` para `.env` e configure as variaveis:

```bash
cp .env.example .env
```

### Gerar hash de senha

```bash
python scripts/generate_password_hash.py sua-senha-aqui
```

Copie o HASH e SALT gerados para o arquivo `.env`.

## Uso

```bash
python run.py
```

Acesse `http://localhost:8000` no navegador.

## Variaveis de Ambiente

| Variavel | Descricao | Padrao |
|----------|-----------|--------|
| `HORA_DAILY_TARGET_MINUTES` | Meta diaria em minutos | 480 |
| `HORA_DATA_DIR` | Diretorio dos arquivos CSV | data |
| `HORA_LOG_LEVEL` | Nivel de log (DEBUG, INFO, WARNING, ERROR) | INFO |
| `HORA_ENVIRONMENT` | Ambiente (development, production) | development |
| `HORA_AUTH_PASSWORD_HASH` | Hash da senha (bcrypt) | (obrigatorio) |
| `HORA_AUTH_BCRYPT_ROUNDS` | Custo do bcrypt para gerar novos hashes | 12 |

## Testes

```bash
pip install -r requirements-dev.txt
pytest
```

## Estrutura do Projeto

```
app/
  domain/         Modelos de dominio e value objects
  use_cases/      Casos de uso da aplicacao
  infrastructure/ Repositorio CSV
  interfaces/     Rotas web e templates
tests/
  unit/           Testes unitarios
  integration/    Testes de integracao
scripts/          Scripts utilitarios
data/             Arquivos CSV (gitignored)
```

## Licenca

MIT License. Veja [LICENSE](LICENSE) para detalhes.
