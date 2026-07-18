# BrownDust2Manager

BrownDust2Manager 是一个面向 Root Android 模拟器的 PySide6 桌面 Root 恢复器，用于扫描棕色尘埃 2（Brown Dust 2）账号备份目录，并通过 ADB Root Shell 恢复账号 shared_prefs。

## 功能

- 仅支持 Root Android 模拟器，并将恢复流程统一收口到 `RootService`。
- 支持配置 1~4 号模拟器的名称、adb serial 和 BrownDust2 Root 目录。
- 提供“连接模拟器”“刷新设备”“检测Root”按钮；刷新设备会执行 `adb devices` 并展示设备名称、serial、online/offline 状态、Root 状态和 Android 版本。
- 恢复时依次检测 Root、停止游戏、删除旧 `shared_prefs`、push 账号 `shared_prefs`、Root Shell 复制、restorecon/chown/chmod、sync 并启动游戏。
- 日志窗口实时显示 adb 命令、执行结果、错误信息和耗时；进度显示 10%、30%、60%、90%、100%。
- 采用 MVC 分层：Model 管理账号和模拟器配置，View 管理界面，Controller 连接交互和业务服务。

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
