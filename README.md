# hxrchk

Bot de demonstração para o comando `/chkall` do Telegram.

## Requisitos

- Python 3.11+
- `python-telegram-bot==20.7`

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuração

Defina a variável de ambiente:

```bash
export TELEGRAM_BOT_TOKEN="SEU_TOKEN_AQUI"
```

## Execução

```bash
python start.py
```

## Comandos

- `/start` — mensagem inicial
- `/chkall 411111` — gera um resultado demonstrativo LIVE ou DIE
- `/chkall 400000 DIE` — força o status DIE

Observação: os resultados são simulados e nunca representam validação real de cartão, aprovação financeira ou autorização.
