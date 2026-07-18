from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


class VerifyService:
    """Verifies and repairs required BrownDust2 player prefs XML keys."""

    PLAYER_PREFS = "com.neowizgames.game.browndust2.v2.playerprefs.xml"
    REQUIRED_KEYS = ("game_data_version", "bundle_version", "BuildPlayerVersion", "unity.cloud_userid")

    def verify(self, shared_prefs: Path) -> list[str]:
        xml_path = shared_prefs / self.PLAYER_PREFS
        if not xml_path.exists():
            return list(self.REQUIRED_KEYS)
        try:
            root = ET.parse(xml_path).getroot()
        except ET.ParseError:
            return list(self.REQUIRED_KEYS)
        present = {node.attrib.get("name") for node in root}
        return [key for key in self.REQUIRED_KEYS if key not in present]

    def repair(self, shared_prefs: Path, defaults: dict[str, str] | None = None) -> None:
        shared_prefs.mkdir(parents=True, exist_ok=True)
        xml_path = shared_prefs / self.PLAYER_PREFS
        defaults = defaults or {}
        if xml_path.exists():
            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()
            except ET.ParseError:
                root = ET.Element("map")
                tree = ET.ElementTree(root)
        else:
            root = ET.Element("map")
            tree = ET.ElementTree(root)
        present = {node.attrib.get("name") for node in root}
        for key in self.REQUIRED_KEYS:
            if key not in present:
                ET.SubElement(root, "string", {"name": key}).text = defaults.get(key, "")
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)

    def verify_and_repair(self, shared_prefs: Path, defaults: dict[str, str] | None = None) -> list[str]:
        missing = self.verify(shared_prefs)
        if missing:
            self.repair(shared_prefs, defaults)
        return self.verify(shared_prefs)
