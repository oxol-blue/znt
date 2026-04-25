# 使用 uv 管理项目

本文档说明如何使用 [uv](https://docs.astral.sh/uv/) 管理智慧校园后端项目。

## 什么是 uv？

uv 是一个用 Rust 编写的极速 Python 包管理器和环境管理工具：
- ⚡ **极速**: 比 pip 快 10-100 倍
- 📦 **统一**: 替代 pip + virtualenv + pip-tools
- 🔒 **锁定**: 内置 lock 文件确保环境一致性
- 🐍 **版本管理**: 自动安装和管理 Python 版本

## 安装 uv

### Windows
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### macOS/Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 常用命令

### 1. 创建虚拟环境并安装依赖
```bash
cd backend

# 创建虚拟环境（会自动使用 .python-version 指定的版本）
uv venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 安装所有依赖（包括锁定版本）
uv pip install -e .

# 或者使用 sync 从 uv.lock 安装（推荐）
uv sync
```

### 2. 添加新依赖
```bash
# 添加运行时依赖
uv add flask-sqlalchemy

# 添加开发依赖
uv add --dev pytest

# 添加可选依赖组
uv add --optional dev black
```

### 3. 更新依赖
```bash
# 更新所有依赖并重新生成 uv.lock
uv lock --upgrade

# 更新单个包
uv lock --upgrade-package flask
```

### 4. 运行项目
```bash
# 使用 uv run（无需手动激活虚拟环境）
uv run python app.py

# 或者使用 gunicorn 生产环境
uv run gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 5. 锁定依赖
```bash
# 根据 pyproject.toml 生成 uv.lock
uv lock

# 验证 lock 文件是否最新
uv lock --locked
```

## 项目结构

```
backend/
├── pyproject.toml       # 项目配置和依赖声明
├── uv.lock             # 锁定依赖精确版本（自动生成）
├── .python-version     # 指定 Python 版本
└── .venv/              # uv 创建的虚拟环境
```

## 生产环境部署

### 使用 uv 部署到宝塔

1. **安装 uv**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **克隆代码并安装依赖**
```bash
cd /www/wwwroot/smart-campus/backend

# 创建虚拟环境并安装（不使用系统 Python）
uv venv --python 3.12
uv sync --no-dev
```

3. **启动命令**
```bash
# 宝塔面板启动命令改为：
cd /www/wwwroot/smart-campus/backend && uv run gunicorn -w 4 -b 127.0.0.1:5000 app:app
```

### Docker 部署（可选）

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# 复制项目文件
COPY pyproject.toml uv.lock ./
COPY backend/ ./backend/

# 安装依赖
RUN uv sync --no-dev

# 暴露端口
EXPOSE 5000

# 启动
CMD ["uv", "run", "gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## 迁移指南（从 pip）

如果你之前使用 requirements.txt：

```bash
# 1. 安装 uv
pip install uv

# 2. 迁移依赖（自动生成 pyproject.toml）
uv pip compile requirements.txt -o pyproject.toml

# 3. 或者手动创建 pyproject.toml 后锁定
uv lock

# 4. 删除旧文件
rm requirements.txt
```

## 高级用法

### Python 版本管理
```bash
# 安装特定 Python 版本
uv python install 3.11 3.12

# 切换项目 Python 版本
echo "3.11" > .python-version
uv sync
```

### 工具运行
```bash
# 无需安装直接运行工具
uv run --with black black .
uv run --with pytest pytest
```

### 环境导出
```bash
# 导出为 requirements.txt（兼容传统部署）
uv export --format requirements-txt > requirements.txt

# 导出生产环境依赖
uv export --no-dev --format requirements-txt > requirements-prod.txt
```

## 最佳实践

1. **始终提交 uv.lock**: 确保团队使用完全相同的依赖版本
2. **使用 .python-version**: 明确项目 Python 版本
3. **分离 dev 依赖**: 开发工具放入 [project.optional-dependencies]
4. **使用 uv run**: 避免手动激活虚拟环境
5. **CI/CD 中使用 uv**: 大幅提升构建速度

## 与传统工具对比

| 操作 | pip + venv | uv |
|------|-----------|-----|
| 创建环境 | `python -m venv .venv` | `uv venv` |
| 安装依赖 | `pip install -r requirements.txt` | `uv sync` |
| 添加依赖 | 手动编辑文件 | `uv add package` |
| 锁定版本 | `pip freeze > requirements.txt` | `uv lock` |
| 运行命令 | `source .venv/bin/activate && python` | `uv run python` |
| 速度 | 慢 | ⚡ 极快 |

## 问题排查

### uv 命令找不到
```bash
# 重新安装或检查 PATH
which uv
# 或
uv --version
```

### 锁定失败
```bash
# 清理缓存重试
uv cache clean
uv lock
```

### 版本冲突
```bash
# 查看依赖树
uv tree

# 强制重新解析
uv lock --upgrade
```

## 参考

- [uv 官方文档](https://docs.astral.sh/uv/)
- [GitHub 仓库](https://github.com/astral-sh/uv)
