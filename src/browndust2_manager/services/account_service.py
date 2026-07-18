from __future__ import annotations

import shutil
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

from browndust2_manager.models.account import Account
from browndust2_manager.repositories.account_repository import AccountRepository
from browndust2_manager.services.account_scanner import AccountScanner


@dataclass(frozen=True, slots=True)
class IntegrityResult:
    """账号文件完整性检测结果。"""

    ok: bool
    messages: list[str]


class AccountService:
    """账号管理业务：扫描、搜索、检测、导入和导出。"""

    def __init__(self, scanner: AccountScanner, repository: AccountRepository) -> None:
        self.scanner = scanner
        self.repository = repository

    def scan_and_sync(self, root: Path) -> list[Account]:
        """扫描账号目录并自动同步 SQLite 数据库。"""
        synced: list[Account] = []
        for account in self.scanner.scan(root):
            synced.append(self.repository.upsert_scanned_account(account))
        return sorted(synced, key=lambda item: item.account_name.lower())

    def search(self, keyword: str = "", favorite: bool | None = None, status: str | None = None) -> list[Account]:
        """按关键词、收藏和状态筛选账号。"""
        accounts = self.repository.list_accounts()
        normalized = keyword.casefold().strip()
        if normalized:
            accounts = [a for a in accounts if normalized in a.account_name.casefold() or normalized in a.remark.casefold() or normalized in str(a.folder_path).casefold()]
        if favorite is not None:
            accounts = [a for a in accounts if a.favorite is favorite]
        if status:
            accounts = [a for a in accounts if a.status == status]
        return accounts

    def find_duplicates(self) -> dict[str, list[Account]]:
        """按 unity_cloud_userid 和账号名检测重复账号。"""
        groups: dict[str, list[Account]] = defaultdict(list)
        for account in self.repository.list_accounts():
            key = account.unity_cloud_userid or account.account_name.casefold()
            groups[key].append(account)
        return {key: value for key, value in groups.items() if len(value) > 1}

    def check_shared_prefs(self, account: Account) -> IntegrityResult:
        """检测 shared_prefs 目录是否存在且包含 XML。"""
        prefs = account.folder_path / "shared_prefs"
        if not prefs.is_dir():
            return IntegrityResult(False, ["缺少 shared_prefs 目录"])
        if not list(prefs.glob("*.xml")):
            return IntegrityResult(False, ["shared_prefs 中没有 XML 文件"])
        return IntegrityResult(True, ["shared_prefs 完整"])

    def check_xml(self, account: Account) -> IntegrityResult:
        """解析所有 XML 文件并报告损坏文件。"""
        messages: list[str] = []
        for xml_file in (account.folder_path / "shared_prefs").glob("*.xml"):
            try:
                ElementTree.parse(xml_file)
            except ElementTree.ParseError as exc:
                messages.append(f"{xml_file.name}: {exc}")
        return IntegrityResult(not messages, messages or ["XML 完整"])

    def import_zip(self, zip_path: Path, destination: Path) -> Account:
        """导入账号 ZIP 到账号目录。"""
        target = destination / zip_path.stem
        target.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(target)
        return self.repository.upsert_scanned_account(self.scanner.account_from_folder(target))

    def export_zip(self, account: Account, output_dir: Path) -> Path:
        """导出账号目录为 ZIP。"""
        output_dir.mkdir(parents=True, exist_ok=True)
        archive_base = output_dir / account.account_name
        archive = shutil.make_archive(str(archive_base), "zip", account.folder_path)
        return Path(archive)
