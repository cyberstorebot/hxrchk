import logging
import os
import random
import re
from typing import Iterable

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def validate_bin(raw_value: str) -> str:
    value = (raw_value or "").strip()
    if not re.fullmatch(r"\d{4,8}", value):
        raise ValueError("BIN inválido. Informe um valor parcial com 4 a 8 dígitos numéricos.")
    return value


def pick_status(preferred_status: str | None = None) -> str:
    candidate = (preferred_status or "").strip().upper()
    if candidate in {"LIVE", "DIE"}:
        return candidate
    return random.choice(["LIVE", "DIE"])


def build_user_label(update: Update) -> str:
    user = update.effective_user
    if user and user.username:
        return f"@{user.username}"
    if user:
        return f"ID {user.id}"
    return "ID desconhecido"


def render_chkall_result(status: str, bin_value: str, verified_by: str) -> str:
    if status == "LIVE":
        icon = "✅"
        banner = "Visa (EXEMPLO)"
        level = "GOLD (EXEMPLO)"
        return_code = "00 (FICTÍCIO)"
    else:
        icon = "❌"
        banner = "EXEMPLO"
        level = "CLASSIC (EXEMPLO)"
        return_code = "51 (FICTÍCIO)"

    return "\n".join(
        [
            f"{icon} CHKALL — {status}",
            "┌─ RESULTADO ─┐",
            f"│ Status: {status} (SIMULADO)",
            f"│ BIN: {bin_value}",
            f"│ Bandeira: {banner}",
            f"│ Nível: {level}",
            f"│ Retorno: {return_code}",
            "│",
            "│ Resultado enviado no chat do usuário!",
            f"│ Verificado por: {verified_by}",
            "└───────────────────────────┘",
            "",
            "Checked by @CYBERTEAM",
        ]
    )


def render_result_list(results: Iterable[dict], verified_by: str, limit: int = 10) -> str:
    limited_results = list(results)[:limit]
    if not limited_results:
        return "Nenhum resultado simulado gerado."

    lines = ["📋 CHKALL — RESULTADOS SIMULADOS"]
    for index, item in enumerate(limited_results, start=1):
        status = str(item.get("status", "LIVE")).upper()
        bin_value = validate_bin(str(item.get("bin", "411111")))
        lines.append(f"{index}. {render_chkall_result(status, bin_value, verified_by)}")

    if len(list(results)) > limit:
        lines.append(f"... e mais {len(list(results)) - limit} resultados simulados")

    return "\n\n".join(lines)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Bem-vindo ao hxrchk. Use /chkall 411111 para gerar um resultado demonstrativo."
    )


async def chkall_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.effective_message.reply_text(
            "❌ Informe um BIN parcial com 4 a 8 dígitos para simular a verificação."
        )
        return

    try:
        bin_value = validate_bin(context.args[0])
        status = pick_status(context.args[1] if len(context.args) > 1 else None)
        verified_by = build_user_label(update)
        message = render_chkall_result(status, bin_value, verified_by)

        try:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        except Exception:
            logger.exception("Falha ao tentar enviar a resposta do /chkall.")
            await update.effective_message.reply_text(
                "❌ Não foi possível enviar a mensagem de resultado. Tente novamente mais tarde."
            )
    except ValueError as exc:
        await update.effective_message.reply_text(f"❌ {exc}")


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("A variável TELEGRAM_BOT_TOKEN não foi definida.")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("chkall", chkall_command))

    application.run_polling()


if __name__ == "__main__":
    main()
