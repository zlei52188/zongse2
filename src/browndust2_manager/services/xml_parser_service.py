from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree


class XmlParserService:
    """Reads BrownDust2 XML preference values."""

    PLAYER_PREFS_FILENAME = "com.neowizgames.game.browndust2.v2.playerprefs.xml"
    KEYS = (
        "BuildPlayerVersion",
        "game_data_version",
        "bundle_version",
        "unity.cloud_userid",
        "Firebase User",
    )

    def parse_player_prefs(self, xml_path: Path) -> dict[str, str]:
        if not xml_path.exists() or not xml_path.is_file():
            return {}

        try:
            root = ElementTree.parse(xml_path).getroot()
        except ElementTree.ParseError:
            return {}

        values: dict[str, str] = {}
        for element in root.iter():
            name = element.attrib.get("name") or element.attrib.get("key")
            if name in self.KEYS:
                values[name] = element.attrib.get("value") or (element.text or "")
        return values
