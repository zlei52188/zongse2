from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import difflib
import xml.etree.ElementTree as ET


@dataclass(frozen=True, slots=True)
class XmlVersionConfig:
    game_data_version: str
    bundle_version: str
    build_player_version: str


@dataclass(frozen=True, slots=True)
class XmlRepairPreview:
    path: Path
    before: str
    after: str
    diff: str


class XmlRepairService:
    """Repairs BrownDust2 player prefs XML files."""

    PLAYER_PREFS_FILENAME = "com.neowizgames.game.browndust2.v2.playerprefs.xml"

    def find_player_prefs(self, account_path: Path) -> Path:
        direct = account_path / self.PLAYER_PREFS_FILENAME
        if direct.is_file():
            return direct
        matches = sorted(account_path.rglob(self.PLAYER_PREFS_FILENAME))
        if matches:
            return matches[0]
        raise FileNotFoundError(f"未找到 XML：{self.PLAYER_PREFS_FILENAME}")

    def preview_account(self, account_path: Path, config: XmlVersionConfig) -> XmlRepairPreview:
        xml_path = self.find_player_prefs(account_path)
        before = xml_path.read_text(encoding="utf-8")
        after = self.repair_text(before, config)
        diff = "".join(
            difflib.unified_diff(
                before.splitlines(keepends=True),
                after.splitlines(keepends=True),
                fromfile=f"{xml_path.name} (恢复前)",
                tofile=f"{xml_path.name} (恢复后)",
            )
        )
        return XmlRepairPreview(path=xml_path, before=before, after=after, diff=diff)

    def repair_account(self, account_path: Path, config: XmlVersionConfig) -> XmlRepairPreview:
        preview = self.preview_account(account_path, config)
        if preview.before != preview.after:
            preview.path.write_text(preview.after, encoding="utf-8")
        return preview

    def repair_text(self, xml_text: str, config: XmlVersionConfig) -> str:
        root = ET.fromstring(xml_text)
        if root.tag != "map":
            map_element = root.find("map")
            if map_element is None:
                raise ValueError("XML 中未找到 <map> 节点")
        else:
            map_element = root

        values = {
            "game_data_version": config.game_data_version,
            "bundle_version": config.bundle_version,
            "BuildPlayerVersion": config.build_player_version,
        }
        children = list(map_element)
        kept: list[ET.Element] = []
        for child in children:
            if child.tag == "string" and child.get("name") in values:
                continue
            kept.append(child)

        game_node = self._string_element("game_data_version", values["game_data_version"])
        bundle_node = self._string_element("bundle_version", values["bundle_version"])
        build_node = self._string_element("BuildPlayerVersion", values["BuildPlayerVersion"])

        map_element[:] = [game_node, *kept, bundle_node, build_node]
        self._indent(root)
        result = ET.tostring(root, encoding="unicode", short_empty_elements=True)
        if xml_text.startswith("<?xml"):
            result = '<?xml version="1.0" encoding="utf-8"?>\n' + result
        if xml_text.endswith("\n"):
            result += "\n"
        return result

    @staticmethod
    def _string_element(name: str, value: str) -> ET.Element:
        element = ET.Element("string", {"name": name})
        element.text = value
        return element

    def _indent(self, element: ET.Element, level: int = 0) -> None:
        indent_text = "\n" + level * "    "
        child_indent = "\n" + (level + 1) * "    "
        if len(element):
            if not element.text or not element.text.strip():
                element.text = child_indent
            for child in element:
                self._indent(child, level + 1)
            if not element[-1].tail or not element[-1].tail.strip():
                element[-1].tail = indent_text
        if level and (not element.tail or not element.tail.strip()):
            element.tail = indent_text
