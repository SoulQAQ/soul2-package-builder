# Installer Builder

[English](README.md) | [中文](README.zh-CN.md)

A professional Windows installer generation tool with project configuration management, auto versioning, file scanning and build pipeline.

## Features

- **Project Management**: Create / Save / Save As / Open installer projects (.ssc format)
- **Installation Config**: App name, version, publisher, main executable, install dir, output dir
- **Auto Versioning**: Increment patch / minor / major version after build
- **File Scanning**: Select source directory, auto scan files and executables
- **Shortcuts**: Desktop shortcut, Start menu shortcut, Uninstaller
- **Simulated Build**: Complete build pipeline (future NSIS / Inno Setup integration)

## Tech Stack

- **Backend**: Python 3.13 + pywebview 6.x
- **Frontend**: Vanilla HTML/CSS/JS (no framework)
- **Data Storage**: Local JSON files (.ssc project format)

## Requirements

- Windows 10/11
- Python 3.13

## Quick Start

### Using UV (Recommended)

```bash
pip install uv
start-uv.bat
```

### Using pip

```bash
setup.bat
start.bat
```

### Manual Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python script/gui.py
```

## Project Structure

```
project-root/
├── script/
│   ├── gui.py                 # GUI entry & API bridge
│   ├── core.py                # Core business logic
│   ├── project_manager.py     # Project manager
│   ├── version_manager.py     # Version manager
│   └── build_system/          # Build system
│       ├── builder.py         # Builder
│       ├── manifest.py        # Build manifest
│       ├── pipeline.py        # Build pipeline
│       └── task_runner.py     # Task runner
├── webui/
│   └── index.html             # Frontend page
├── data/
│   └── projects/              # Project files (.ssc)
├── config/
│   └── settings.json          # App config
├── output/                    # Build output
├── requirements.txt
├── setup.bat
├── start.bat
├── start-uv.bat
└── build.bat
```

## Build to EXE

```bash
build.bat
```

## License

[GPL-3.0](LICENSE)
