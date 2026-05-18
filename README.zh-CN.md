# 安装包生成器

[English](README.md) | [中文](README.zh-CN.md)

一款专业的 Windows 安装程序生成工具，支持项目配置管理、版本号自动递增、文件扫描和安装包构建。

## 功能特性

- **项目管理**：新建 / 保存 / 另存为 / 打开安装项目（.ssc 格式）
- **安装配置**：应用名称、版本号、发布者、主程序、安装目录、输出目录
- **自动版本号**：构建后自动递增修订版本 / 次版本 / 主版本
- **文件扫描**：选择源目录，自动扫描文件和 EXE
- **快捷方式**：桌面快捷方式、开始菜单快捷方式、卸载程序
- **模拟构建**：完整构建管线流程（未来接入 NSIS / Inno Setup）

## 技术栈

- **后端**：Python 3.13 + pywebview 6.x
- **前端**：原生 HTML/CSS/JS（无框架依赖）
- **数据存储**：本地 JSON 文件（.ssc 项目格式）

## 系统要求

- Windows 10/11
- Python 3.13

## 快速启动

### 使用 UV（推荐）

```bash
pip install uv
start-uv.bat
```

### 使用 pip

```bash
setup.bat
start.bat
```

### 手动安装

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python script/gui.py
```

## 项目结构

```
project-root/
├── script/
│   ├── gui.py                 # GUI 入口与 API 桥接
│   ├── core.py                # 核心业务逻辑
│   ├── project_manager.py     # 项目管理器
│   ├── version_manager.py     # 版本号管理器
│   └── build_system/          # 构建系统
│       ├── builder.py         # 构建器
│       ├── manifest.py        # 构建清单
│       ├── pipeline.py        # 构建管线
│       └── task_runner.py     # 任务运行器
├── webui/
│   └── index.html             # 前端页面
├── data/
│   └── projects/              # 项目文件（.ssc）
├── config/
│   └── settings.json          # 应用配置
├── output/                    # 构建输出
├── requirements.txt
├── setup.bat
├── start.bat
├── start-uv.bat
└── build.bat
```

## 打包为 EXE

```bash
build.bat
```

## 许可证

[GPL-3.0](LICENSE)
