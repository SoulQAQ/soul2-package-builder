# WC3 技能文本生成器

[English](README.md) | [中文](README.zh-CN.md)

一款用于生成魔兽争霸3(WC3)技能描述文本的桌面应用程序，支持自定义颜色代码。

## 功能特性

- **技能编辑器**：编辑技能属性（名称、热键、效果、属性参数）
- **实时预览**：WC3 tooltip样式的实时预览
- **数值参数编辑**：支持参数表、`a=100+10` 递增公式和 `a=100,120,150` 逐级数值
- **颜色配置**：自定义5种颜色元素，支持保存/加载预设方案
- **文本生成**：一键复制带WC3颜色代码（`|cffXXXXXX`）的文本
- **分类管理**：树形资源管理器，支持2-3层嵌套分类
- **导入导出**：批量JSON导入导出

## 技术栈

- **后端**：Python 3.13 + pywebview
- **前端**：原生 HTML/CSS/JS（无框架依赖）
- **数据存储**：本地JSON文件，存储在 `/data/` 目录

## 系统要求

- Python 3.13（Python 3.14 不支持，pythonnet尚未兼容）
- uv 包管理器（推荐）或 pip

## 快速启动

### 使用 UV（推荐）

```bash
# 安装 uv（如未安装）
pip install uv

# 运行启动脚本
start-uv.bat
```

### 使用 pip

```bash
# 运行环境安装脚本（需要 Python 3.13）
setup.bat

# 启动程序
start.bat
```

### 手动安装

```bash
# 创建 Python 3.13 虚拟环境
python -m venv .venv

# 激活并安装依赖
.venv\Scripts\activate
pip install -r requirements.txt

# 运行应用
python script/gui.py
```

## 项目结构

```
project-root/
├── script/
│   └── gui.py              # 后端入口与API
├── webui/
│   └── index.html          # 前端页面（HTML/CSS/JS）
├── data/
│   ├── spells/             # 技能JSON文件（按分类存储）
│   ├── colors/             # 颜色配置预设
│   ├── exports/            # 导出文件
│   └── settings.json       # 应用设置
├── config/
│   └── setting.yaml        # 配置文件
├── docs/
│   ├── PROJECT_ARCHITECTURE.md
│   └── TECHNICAL_DESIGN.md
├── requirements.txt
├── setup.bat               # 环境安装脚本
├── start.bat               # 启动脚本
├── start-uv.bat            # UV启动脚本
├── build.bat               # 打包脚本
└── README.md
```

## 数据存储

技能以JSON文件形式存储在 `/data/spells/` 目录，按分类层级组织：

```
data/spells/
├── 英雄/
│   ├── 圣骑士/
│   │   ├── 圣光.json
│   │   └── 神圣护盾.json
│   └── 大法师/
│       └── 暴风雪.json
└── 物品/
    └── 传送卷轴.json
```

## 颜色配置

可自定义以下颜色元素：
- **热键颜色**：技能热键文字颜色
- **学习等级颜色**：学习模式下的等级文字颜色
- **属性名称颜色**：法力消耗、冷却时间等属性名颜色
- **升级等级颜色**：升级描述中的等级前缀颜色
- **特殊描述颜色**：如"需要持续施法"等特殊说明颜色

颜色预设保存在 `/data/colors/` 目录下。

## 使用说明

1. **创建分类**：点击左侧边栏的"+ 分类"按钮创建技能文件夹
2. **编辑技能**：在右侧面板填写技能属性
3. **数值参数**：在描述中写 `{a}`，再用参数表定义基础值、每级增量或逐级数值
4. **预览效果**：左侧面板实时显示WC3 tooltip样式预览
5. **生成文本**：点击"生成"按钮复制带颜色代码的文本
6. **保存技能**：保存到选定的分类中

## 数值参数

```
a=100+10；b=3,4,5
```

- 技能等级数量来自编辑器里的“技能等级”输入框
- `a=基础值+增量`：公式，每级增加增量值
- `b=值1,值2,值3`：显式列表，直接指定每级的值
- 旧版 `[lv=3][a=100+10]` 仍可读取，但 `lv` 只作为历史兼容，不再控制等级数量

描述文本中使用 `{a}` 引用参数 `a` 的值。

## 打包为 EXE

```bash
build.bat
```

或手动打包：
```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --add-data "webui;webui" --add-data "config;config" --icon "app.ico" script/gui.py
```

## 许可证

[GPL-3.0](LICENSE)
