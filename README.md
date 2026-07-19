# BrownDust2Manager

BrownDust2Manager 是一个面向长期使用的 BrownDust2 Root 游客号恢复管理器。项目采用 PySide6 桌面界面，并按 MVC、Service、Repository 分层组织：界面只负责展示与交互转发，业务逻辑集中在 Service，SQLite 持久化集中在 Repository。

## 当前能力

### 账号数据库

- 启动后在当前工作目录创建 `accounts.db`。
- `accounts` 表包含：`id`、`account_name`、`folder_path`、`unity_cloud_userid`、`game_data_version`、`bundle_version`、`BuildPlayerVersion`、`last_restore_time`、`favorite`、`remark`、`status`、`restore_count`、`color_label`、`created_at`、`updated_at`。
- 扫描账号目录时会自动 upsert 到 SQLite，并保留收藏、备注、颜色标签、恢复次数等管理字段。

### 账号管理

- 支持收藏、备注、颜色标签的仓库接口。
- 支持关键词搜索、收藏筛选、状态筛选。
- 支持按 `unity_cloud_userid` 或账号名检测重复账号。
- 支持 `shared_prefs` 完整性检测和 XML 解析完整性检测。
- 支持账号 ZIP 导入和导出。

### 模拟器管理

- `EmulatorService` 支持无限模拟器的新增、删除、修改、列表维护。
- 每个模拟器记录名称、ADB Serial、ADB Port、Android Version、Root、在线状态、游戏状态、恢复次数、最后恢复时间。
- 支持 ADB 连接测试与 `adb devices` 自动发现设备。

### 恢复中心

恢复流程由 `RestoreService` 统一编排：

1. 停止游戏。
2. 备份 `shared_prefs`。
3. 校验/修复 XML。
4. 恢复 `shared_prefs`。
5. 恢复权限。
6. 校验恢复源。
7. 启动游戏。
8. 等待启动完成。
9. 失败自动重试 3 次。

### 任务中心

- `TaskService` 支持创建恢复任务、开始、暂停、继续、停止、删除。
- 任务记录包含状态、进度、耗时，可作为恢复记录使用。

### 日志

- `LogService` 默认写入 `logs/`。
- 每天一个日志文件，支持错误日志、ADB 日志、恢复日志、XML 日志分类。
- 支持日志关键词搜索，日志目录可通过设置服务配置。

### 设置

- `SettingsService` 支持账号目录、ADB 路径、默认模拟器、默认恢复方式、默认 XML 版本、日志目录、备份目录、自动备份、自动修复 XML。

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
  controllers/           # Controller 层，只连接界面和服务
  models/                # Model 层，数据结构和 Qt Model
  repositories/          # Repository 层，SQLite 持久化
  services/              # Service 层，账号、恢复、模拟器、任务、日志、设置业务
  views/                 # View 层，只包含界面逻辑
```

## 测试

```bash
pytest -q
```
