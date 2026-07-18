# BrownDust2Manager

BrownDust2Manager 是一个面向 Windows 的 PySide6 桌面工程，用于扫描棕色尘埃 2（Brown Dust 2）账号备份目录，并通过左侧账号列表对账号执行恢复操作。

## 功能

- 启动时自动扫描默认账号目录 `%USERPROFILE%\Documents\BrownDust2Accounts`。
- 顶部提供“选择目录...”和“刷新”按钮，可切换目录并重新扫描。
- 左侧账号列表显示账号文件夹名称、最后修改时间，以及 `shared_prefs` 是否存在。
- 双击账号会在系统资源管理器中打开该账号文件夹。
- 右键账号弹出菜单，可选择恢复到 1~4 号模拟器。
- 采用 MVC 分层：Model 管理数据，View 管理界面，Controller 连接交互和业务服务。
- 预留 `restore_account(account_path, emulator_id)` 作为实际恢复逻辑入口。

## 安装与运行

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
browndust2-manager
# 或：python -m browndust2_manager
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
  services/              # 扫描与恢复业务服务
  views/                 # PySide6 View 层
```
