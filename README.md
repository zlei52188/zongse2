# BrownDust2Manager

BrownDust2Manager 是一个面向 Windows 的 PySide6 桌面工程，用于扫描棕色尘埃 2（Brown Dust 2）账号备份目录，并通过左侧账号列表对账号执行恢复操作。

## 功能

- 扫描指定账号目录，并列出所有账号文件夹。
- 左侧账号列表显示账号名称、路径和修改时间。
- 右键账号弹出菜单，可选择“恢复到模拟器1”到“恢复到模拟器4”。
- 可保存 1~4 号模拟器的 BrownDust2 数据目录配置，默认目录为 `/data/data/com.neowizgames.game.browndust2`。
- 恢复账号时会删除目标 `shared_prefs`，复制账号备份中的 `shared_prefs`，并尽量保留文件权限与元数据。
- 加入日志窗口，实时显示删除、复制和恢复完成状态。
- 采用 MVC 分层：Model 管理数据，View 管理界面，Controller 连接交互和业务服务。
- 所有恢复文件操作封装在 `RestoreService`。

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
  services/              # 扫描与恢复业务服务
  views/                 # PySide6 View 层
```


## 模拟器数据目录配置

点击工具栏“模拟器目录配置...”可分别保存 1~4 号模拟器的数据目录。每个目录应指向 BrownDust2 的应用数据目录，例如：

```text
/data/data/com.neowizgames.game.browndust2
```

配置默认保存到 `~/.config/BrownDust2Manager/settings.json`。也可以通过环境变量 `BROWNDUST2_MANAGER_CONFIG` 指定配置文件路径。
