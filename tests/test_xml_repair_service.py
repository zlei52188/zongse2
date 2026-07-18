from __future__ import annotations

import xml.etree.ElementTree as ET

from browndust2_manager.services.xml_repair_service import XmlRepairService, XmlVersionConfig

CONFIG = XmlVersionConfig("gd", "bundle", "build")


def names(xml_text: str) -> list[str | None]:
    root = ET.fromstring(xml_text)
    return [child.get("name") for child in root if child.tag == "string"]


def value(xml_text: str, key: str) -> str | None:
    root = ET.fromstring(xml_text)
    for child in root:
        if child.tag == "string" and child.get("name") == key:
            return child.text
    return None


def test_repairs_existing_fields():
    xml = """<map>
    <string name="game_data_version">old</string>
    <int name="x" value="1" />
    <string name="bundle_version">old</string>
    <string name="BuildPlayerVersion">old</string>
</map>
"""

    repaired = XmlRepairService().repair_text(xml, CONFIG)

    assert value(repaired, "game_data_version") == "gd"
    assert value(repaired, "bundle_version") == "bundle"
    assert value(repaired, "BuildPlayerVersion") == "build"


def test_inserts_missing_fields_in_required_order():
    xml = """<map>
    <int name="x" value="1" />
</map>
"""

    repaired = XmlRepairService().repair_text(xml, CONFIG)

    repaired_names = names(repaired)
    assert repaired_names[0] == "game_data_version"
    assert repaired_names[-2:] == ["bundle_version", "BuildPlayerVersion"]


def test_removes_duplicate_version_fields():
    xml = """<map>
    <string name="bundle_version">a</string>
    <string name="game_data_version">a</string>
    <string name="bundle_version">b</string>
    <string name="BuildPlayerVersion">a</string>
    <string name="BuildPlayerVersion">b</string>
</map>
"""

    repaired = XmlRepairService().repair_text(xml, CONFIG)

    assert names(repaired).count("game_data_version") == 1
    assert names(repaired).count("bundle_version") == 1
    assert names(repaired).count("BuildPlayerVersion") == 1


def test_repairs_wrong_order():
    xml = """<map>
    <string name="BuildPlayerVersion">old</string>
    <string name="bundle_version">old</string>
    <int name="x" value="1" />
    <string name="game_data_version">old</string>
</map>
"""

    repaired = XmlRepairService().repair_text(xml, CONFIG)

    repaired_names = names(repaired)
    assert repaired_names[0] == "game_data_version"
    assert repaired_names.index("bundle_version") < repaired_names.index("BuildPlayerVersion")


def test_repair_account_writes_player_prefs(tmp_path):
    account = tmp_path / "account"
    account.mkdir()
    prefs = account / XmlRepairService.PLAYER_PREFS_FILENAME
    prefs.write_text("<map />\n", encoding="utf-8")

    preview = XmlRepairService().repair_account(account, CONFIG)

    assert preview.path == prefs
    assert value(prefs.read_text(encoding="utf-8"), "BuildPlayerVersion") == "build"
