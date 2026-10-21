import logging
import os
import random
import re
from typing import Iterable

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("8843258561:AAE2b6G_y_37tFgnkQOjSfalOuvAFa0LSO0")


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
        raise ValueError("Informe os dados do cartão")
    cleaned = re.sub(r"\s+", "", value)
    if len(cleaned) < 4 or len(cleaned) > 19:
        raise ValueError("Cartão inválido. Use uma numeração com 4 a 19 dígitos.")
    if not cleaned.isdigit():
        raise ValueError("Cartão inválido. Use apenas númerações válidas.")
    return cleaned


def normalize_expiry(mm: str, yy: str) -> tuple[str, str]:
    mm_value = (mm or "").strip()
    yy_value = (yy or "").strip()
    if not re.fullmatch(r"\d{2}", mm_value):
        raise ValueError("MM inválido. Use dois dígitos, exemplo: 12.")
    if not re.fullmatch(r"\d{2,4}", yy_value):
        raise ValueError("YY inválido. Use dois ou quatro dígitos, exemplo: 27.")
    return mm_value, yy_value


def normalize_cvv(raw_cvv: str) -> str:
    cvv = (raw_cvv or "").strip()
    if not re.fullmatch(r"\d{3,4}", cvv):
        raise ValueError("CVV inválido. Use 3 ou 4 dígitos.")
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
        raise ValueError("BIN inválida. Informe um valor parcial com 4 a 8 dígitos numéricos.")
    return value


def pick_status(preferred_status: str | None = None) -> str:
    candidate = (preferred_status or "").strip().upper()
    if candidate in {"LIVE", "DIE"}:
        return candidate
    return random.choice(["LIVE", "DIE"])


def render_chkall_result(status: str, bin_value: str, verified_by: str) -> str:
    if status == "LIVE":
        icon = "✅"
        banner = "Visa"
        level = "GOLD"
        return_code = "00"
    else:
        icon = "❌"
        banner = "MasterCard"
        level = "CLASSIC "
        return_code = "51"

    return "\n".join(
        [
            f"{icon} CHKALL — {status}",
            "┌─ RESULTADO ─┐",
            f"│ Status: {status}",
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
        return "Nenhum resultado gerado."

    lines = ["📋 HaxorCHK — RESULTADOS GERADOS"]
    for index, item in enumerate(limited, start=1):
        status = str(item.get("status", "LIVE")).upper()
        bin_value = validate_bin(str(item.get("bin", "411111")))
        lines.append(f"{index}. {render_chkall_result(status, bin_value, verified_by)}")

    if len(items) > limit:
        lines.append(f"... e mais {len(items) - limit} resultados gerados")

    return "\n\n".join(lines)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Bem-vindo ao Checker da CyberHaxor. Digite /comandos para ver os comandos disponíveis para validar cartões."
    )


async def comandos_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Comandos de usuário:\n"
        "• /chk CARTAO|MM|YY|CVV\n"
        "• /chkall CARTAO|MM|YY|CVV [10 linhas]\n\n"
        "Observação: Digite os comandos no grupo CyberHaxor [Use o tópico ChkCC]."
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
            "Formato: /chkall CARTAO|MM|YY|CVV [Max: 10 linhas]\nExemplo: /chkall 4111111111111111|12|27|123 10"
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
