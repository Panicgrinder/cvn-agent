import os
import json
import builtins
import tempfile
from scripts import customize_prompts as cp


def test_customize_prompts_create_rules():
    with tempfile.TemporaryDirectory() as tmp_root:
        core_dir = os.path.join(tmp_root, "app", "core")
        os.makedirs(core_dir, exist_ok=True)
        # project_root im Modul umlegen
        cp.project_root = tmp_root

    # Simuliere Benutzereingaben für zwei Regeln und 'fertig'
    inputs = iter(["Freundlichkeit: erlaubt", "Beleidigungen: verboten", "fertig"])

    def fake_input(prompt: str = ""):
        return next(inputs)

    # Input patchen und ausführen
    builtins_input_backup = builtins.input
    try:
        builtins.input = fake_input  # type: ignore[assignment]
        cp.create_content_rules()
    finally:
        builtins.input = builtins_input_backup  # wiederherstellen

    # Prüfen
    rules_file = os.path.join(core_dir, "content_rules.json")
    assert os.path.exists(rules_file)
    with open(rules_file, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert data.get("Freundlichkeit") is True
    assert data.get("Beleidigungen") is False
