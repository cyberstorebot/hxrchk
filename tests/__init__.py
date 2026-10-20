from types import SimpleNamespace

import pytest

from start import build_user_label, pick_status, render_chkall_result, render_result_list, validate_bin


@pytest.mark.parametrize(
    ("status", "bin_value", "expected_icon", "expected_return"),
    [
        ("LIVE", "411111", "✅", "00 (FICTÍCIO)"),
        ("DIE", "400000", "❌", "51 (FICTÍCIO)"),
    ],
)
def test_chkall_message_format(status, bin_value, expected_icon, expected_return):
    message = render_chkall_result(status, bin_value, "@usuario")

    assert f"{expected_icon} CHKALL — {status}" in message
    assert f"Status: {status} (SIMULADO)" in message
    assert f"BIN: {bin_value}" in message
    assert "Resultado enviado no chat do usuário!" in message
    assert "Verificado por: @usuario" in message
    assert f"Retorno: {expected_return}" in message
    assert "Checked by @CYBERTEAM" in message


def test_user_name_is_used_when_available():
    update = SimpleNamespace(
        effective_user=SimpleNamespace(username="usuario", id=123456),
        effective_chat=SimpleNamespace(id=987654),
    )

    assert build_user_label(update) == "@usuario"


def test_missing_username_uses_numeric_id():
    update = SimpleNamespace(
        effective_user=SimpleNamespace(username=None, id=123456),
        effective_chat=SimpleNamespace(id=987654),
    )

    assert build_user_label(update) == "ID 123456"


def test_bin_validation_rejects_invalid_value():
    with pytest.raises(ValueError):
        validate_bin("41111A")

    with pytest.raises(ValueError):
        validate_bin("123456789")


def test_result_list_respects_limit_of_ten():
    results = [
        {"status": "LIVE", "bin": "411111"}
        for _ in range(12)
    ]

    message = render_result_list(results, "@usuario", limit=10)
    count = message.count("Status:")

    assert count == 10
    assert "... e mais 2 resultados simulados" in message


def test_simulated_status_is_explicitly_marked_as_fictitious():
    message = render_chkall_result("DIE", "400000", "@usuario")

    assert "(SIMULADO)" in message
    assert "FICTÍCIO" in message
    assert "gateway" not in message.lower()


def test_pick_status_accepts_live_or_die_only():
    assert pick_status("live") == "LIVE"
    assert pick_status("die") == "DIE"
    assert pick_status("random") in {"LIVE", "DIE"}


def test_no_full_card_or_cvv_is_expected():
    message = render_chkall_result("LIVE", "411111", "@usuario")

    assert "411111" in message
    assert "cvv" not in message.lower()
    assert "cartao" not in message.lower()
    assert "numero" not in message.lower()
