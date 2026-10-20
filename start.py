import logging
import os
import random
import re
from typing import Iterable

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("8891474481:AAEzPhza9lRsLgpJ_MBk-9TdULjHx6AyKKg")


def build_user_label(update: Update) -> str:
    user = update.effective_user
    if user and user.username:
        return f"@{user.username}"
    if user:
        return f"ID {user.id}"
    return "ID desconhecido"


def normalize_card_input(raw_value: str) -> str:
    value = (raw_value or "").strip()
    if not value:
        raise ValueError("Informe o cartão para a simulação.")
    cleaned = re.sub(r"\s+", "", value)
    if len(cleaned) < 4 or len(cleaned) > 19:
        raise ValueError("Cartão inválido para simulação. Use um valor fictício com 4 a 19 dígitos.")
    if not cleaned.isdigit():
        raise ValueError("Cartão inválido para simulação. Use apenas dígitos fictícios.")
    return cleaned


def normalize_expiry(mm: str, yy: str) -> tuple[str, str]:
    mm_value = (mm or "").strip()
    yy_value = (yy or "").strip()
    if not re.fullmatch(r"\d{2}", mm_value):
        raise ValueError("MM inválido. Use dois dígitos fictícios, exemplo: 12.")
    if not re.fullmatch(r"\d{2,4}", yy_value):
        raise ValueError("YY inválido. Use dois ou quatro dígitos fictícios, exemplo: 27.")
    return mm_value, yy_value


def normalize_cvv(raw_cvv: str) -> str:
    cvv = (raw_cvv or "").strip()
    if not re.fullmatch(r"\d{3,4}", cvv):
        raise ValueError("CVV inválido. Use 3 ou 4 dígitos fictícios.")
    return cvv


def parse_simulation_payload(args: list[str]) -> tuple[str, str, str, str]:
    if len(args) < 4:
        raise ValueError("Formato incorreto. Use: /chk CARTAO|MM|YY|CVV")

    raw_card, raw_mm, raw_yy, raw_cvv = args[:4]
    card = normalize_card_input(raw_card)
    mm, yy = normalize_expiry(raw_mm, raw_yy)
    cvv = normalize_cvv(raw_cvv)
    return card, mm, yy, cvv


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
    items = list(results)
    limited = items[:limit]
    if not limited:
        return "Nenhum resultado simulado gerado."

    lines = ["📋 CHKALL — RESULTADOS SIMULADOS"]
    for index, item in enumerate(limited, start=1):
        status = str(item.get("status", "LIVE")).upper()
        bin_value = validate_bin(str(item.get("bin", "411111")))
        lines.append(f"{index}. {render_chkall_result(status, bin_value, verified_by)}")

    if len(items) > limit:
        lines.append(f"... e mais {len(items) - limit} resultados simulados")

    return "\n\n".join(lines)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Bem-vindo ao hxrchk. Use /comandos para ver os comandos disponíveis."
    )


async def comandos_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Comandos de usuário:\n"
        "• /chk CARTAO|MM|YY|CVV\n"
        "• /chkall CARTAO|MM|YY|CVV [10 linhas]\n\n"
        "Observação: todos os resultados são demonstrativos e fictícios."
    )
    await update.effective_message.reply_text(text)


async def chk_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.effective_message.reply_text(
            "Formato: /chk CARTAO|MM|YY|CVV\nExemplo: /chk 4111111111111111|12|27|123"
        )
        return

    try:
        card, mm, yy, cvv = parse_simulation_payload(context.args)
        bin_value = card[:6] if len(card) >= 6 else card
        status = pick_status()
        verified_by = build_user_label(update)
        message = render_chkall_result(status, validate_bin(bin_value), verified_by)
        message = message.replace("│ BIN: ", f"│ BIN: {bin_value}\n│ Cartão: {card[-4:]}\n│ MM/YY: {mm}/{yy}\n│ CVV: {cvv}\n│ BIN: ")
        await update.effective_message.reply_text(message)
    except ValueError as exc:
        await update.effective_message.reply_text(f"❌ {exc}")


async def chkall_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.effective_message.reply_text(
            "Formato: /chkall CARTAO|MM|YY|CVV [10 linhas]\nExemplo: /chkall 4111111111111111|12|27|123 5"
        )
        return

    try:
        card, mm, yy, cvv = parse_simulation_payload(context.args[:4])
        limit = 10
        if len(context.args) > 4:
            try:
                limit = int(context.args[4])
            except ValueError:
                limit = 10
        limit = max(1, min(limit, 10))
        verified_by = build_user_label(update)
        results = [
            {"status": pick_status(), "bin": card[:6] if len(card) >= 6 else card}
            for _ in range(limit)
        ]
        message = render_result_list(results, verified_by, limit=limit)
        await update.effective_message.reply_text(message)
    except ValueError as exc:
        await update.effective_message.reply_text(f"❌ {exc}")


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("A variável TELEGRAM_BOT_TOKEN não foi definida.")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("comandos", comandos_command))
    application.add_handler(CommandHandler("chk", chk_command))
    application.add_handler(CommandHandler("chkall", chkall_command))
    application.run_polling()


if __name__ == "__main__":
    main()
