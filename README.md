# BrownDust2Manager

BrownDust2Manager 是一个面向 Windows 的 PySide6 桌面工程，用于扫描棕色尘埃 2（Brown Dust 2）账号备份目录，并通过左侧账号列表对账号执行恢复操作。

## 功能

- 扫描指定账号目录，并列出所有账号文件夹。
- 左侧账号列表显示账号名称、路径和修改时间。
- 右键账号弹出菜单，可选择恢复到 1~4 号模拟器。
- 新增 `RecoveryEngine` 统一恢复流程：扫描账号、XML 修复、停止游戏、备份当前 `shared_prefs`、恢复账号、恢复权限、启动游戏、检测结果。
- 新增 `BackupService`：按 `backup/yyyyMMdd_HHmmss/` 自动备份，支持查看、恢复和删除备份。
- 新增 `VerifyService`：恢复后检查 `com.neowizgames.game.browndust2.v2.playerprefs.xml`，自动补齐 `game_data_version`、`bundle_version`、`BuildPlayerVersion`、`unity.cloud_userid`。
- 新增 `EmulatorManager`：保存 1~4 号模拟器的名称、ADB Serial、Root 路径、Android 版本、Root 状态和在线状态。
- 支持批量恢复到全部模拟器、多个账号恢复队列，以及暂停、继续、取消控制。
- 恢复窗口显示当前账号、当前模拟器、当前步骤、耗时、日志和进度条。
- 失败自动重试最多 3 次，并在批量恢复结束后统计成功数量、失败数量、失败原因，支持导出日志。
- 采用 MVC 分层：Model 管理数据，View 管理界面，Controller 连接交互和业务服务；文件操作放在 Service，ADB 操作集中在 `RootService`，`MainWindow` 只负责 UI。

## 安装与运行

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
browndust2-manager
```

也可以直接运行：

```bash
python -m browndust2_manager
```

## 默认账号目录

程序会优先读取环境变量 `BROWNDUST2_ACCOUNTS_DIR`。如果未设置，则默认使用：

```text
%USERPROFILE%\Documents\BrownDust2Accounts
```

可在界面顶部点击“选择目录...”切换账号目录，然后点击“刷新”重新扫描。

## 工程结构

```text
src/browndust2_manager/
  app.py                 # QApplication 入口
  __main__.py            # python -m 入口
  controllers/           # Controller 层
  models/                # Model 层
  services/              # 扫描、备份、校验、模拟器与恢复业务服务
  views/                 # PySide6 View 层
```
