# Everything Search SOP

## 概述

通过 Everything 实现本地文件高速搜索，支持 CLI 和 HTTP 两种模式。

## 模式优先级

| 优先级 | 模式 | 依赖 | 优点 |
|--------|------|------|------|
| 1 | CLI（内嵌 es.exe） | 无 | 离线可用，无需安装 GUI |
| 2 | HTTP | Everything GUI + HTTP服务器 | 功能完整 |

## 文件结构

```
memory/everything_search/
├── everything_search.py   # 核心脚本（自动检测模式）
├── es.exe                 # Everything CLI 工具（可选）
└── everything_search_sop.md
```

## 快速用法

```python
from memory.everything_search import everything_search

# 基础搜索
results = everything_search("*.py")

# 指定路径+最大数量
results = everything_search("D:\\Project\\*.md", max_results=10)
```

## 返回格式

```python
[
    {'name': 'file.py', 'path': 'C:\\path\\to\\file.py', 'size': '1 KB', 'date': '2025-01-01'},
    ...
]
```

## 工作模式

脚本自动检测，优先级：

| 优先级 | 模式 | 条件 | 优势 |
|--------|------|------|------|
| 1 | **CLI** | `es.exe` 存在于脚本目录 | ✅ 独立运行，无需 Everything GUI |
| 2 | **HTTP** | Everything HTTP 服务运行（端口 8025） | ✅ 实时索引 |

## 搜索语法

| 类型 | 示例 | 说明 |
|------|------|------|
| 路径搜索 | `D:\\Project\\*` | 指定路径下的所有文件 |
| 文件名关键词 | `python` | 匹配文件名包含关键词 |
| 精确搜索 | `"README"` | 精确文件名 |
| 扩展名 | `ext:md` | 按扩展名筛选 |
| 大小 | `size:>1mb` | 按大小筛选 (>1MB) |
| 日期范围 | `dm:2025-01-01..2025-12-31` | 修改日期范围 |
| 通配符 | `*.py` | 匹配任意字符 |
| 多条件组合 | `D:\\Project\\*.py .py` | 多条件搜索 |
| 仅目录 | `folder:` | 仅搜索目录 |
| 仅文件 | `/.py` | 仅搜索文件 |
| 全部 | `*` | 搜索全部索引文件 |

## CLI 工具安装

1. 下载 [ES-1.1.0.30.x64.zip](https://www.voidtools.com/downloads/)
2. 解压得到 `es.exe`
3. 放入 `memory/everything_search/es.exe`

## HTTP 模式配置

1. 启动 Everything GUI
2. 菜单 → 工具 → 选项 → HTTP服务器 → 启用
3. 默认端口：8025

## 注意事项

1. Windows 路径用 `\\` 或 `/`
2. Everything 默认仅索引文件名，需开启"文件夹索引"才能搜索路径
3. CLI 模式更可靠，不依赖 GUI 运行状态
4. es.exe 版本需与 Everything 索引数据库版本匹配