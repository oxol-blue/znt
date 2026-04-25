# uv 项目管理配置汇总

## 快速开始

```bash
# 1. 进入后端目录
cd backend

# 2. 创建虚拟环境并安装依赖
uv sync

# 3. 启动开发服务器
uv run python app.py
```

## 文件说明

| 文件 | 用途 |
|------|------|
| `pyproject.toml` | 项目配置、依赖声明、工具配置 |
| `.python-version` | 指定 Python 版本 (3.12) |
| `uv.lock` | 锁定依赖精确版本（执行 uv sync 后生成） |
| `requirements.txt` | 导出给传统 pip 使用的依赖列表 |
| `UV_README.md` | uv 完整使用文档 |

## 常用命令速查表

### 环境管理
```bash
uv venv                    # 创建虚拟环境
uv venv --python 3.11     # 指定 Python 版本创建
.venv\Scripts\activate     # 激活环境（Windows）
source .venv/bin/activate  # 激活环境（Linux/Mac）
```

### 依赖管理
```bash
uv sync                           # 安装/同步所有依赖
uv sync --no-dev                  # 只安装生产依赖
uv add flask                      # 添加依赖
uv add --dev pytest               # 添加开发依赖
uv remove flask                   # 移除依赖
uv lock                           # 生成 uv.lock
uv lock --upgrade                 # 更新所有依赖
```

### 运行项目
```bash
uv run python app.py              # 运行应用
uv run gunicorn app:app           # 使用 gunicorn
uv run --dev pytest               # 运行测试
uv run black .                    # 代码格式化
```

### 导出依赖
```bash
uv export --format requirements-txt > requirements.txt           # 导出生产依赖
uv export --no-dev --format requirements-txt > requirements.txt  # 同上
uv export --with-dev --format requirements-txt > requirements-dev.txt  # 包含开发依赖
```

## 项目配置亮点

### 1. 现代化工具链集成

`pyproject.toml` 已配置以下工具：

- **black**: 代码格式化（行宽 100）
- **ruff**: 代码检查（替代 flake8 + isort）
- **mypy**: 类型检查
- **pytest**: 测试框架

使用方式：
```bash
uv run black .        # 格式化代码
uv run ruff check .   # 检查代码
uv run ruff fix .     # 自动修复问题
uv run mypy .         # 类型检查
uv run pytest         # 运行测试
```

### 2. 依赖分组

```toml
[project.dependencies]           # 生产依赖
[project.optional-dependencies]
dev = [...]                     # 开发依赖
```

安装时区分：
```bash
uv sync              # 安装所有依赖（含 dev）
uv sync --no-dev     # 只安装生产依赖（部署用）
```

### 3. 脚本命令

```toml
[project.scripts]
smart-campus = "app:main"
```

运行：
```bash
uv run smart-campus    # 等同于 uv run python app.py
```

## 部署建议

### 开发环境
```bash
uv sync                    # 安装所有依赖包括开发工具
uv run python app.py       # 启动开发服务器
```

### 生产环境
```bash
uv sync --no-dev           # 只安装生产依赖
uv run gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker 部署
```dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY backend/ ./backend/

RUN uv sync --no-dev

EXPOSE 5000
CMD ["uv", "run", "gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### 宝塔面板部署

1. 安装 uv
2. 使用 `uv sync --no-dev` 安装依赖
3. 启动命令：`uv run gunicorn -w 4 -b 127.0.0.1:5000 app:app`

## 迁移现有项目

如果项目已使用 requirements.txt：

```bash
# 1. 安装 uv
pip install uv

# 2. 导入现有依赖
uv pip install -r requirements.txt

# 3. 生成 pyproject.toml 和 uv.lock
uv pip compile requirements.txt -o pyproject.toml
# 或手动创建 pyproject.toml

# 4. 锁定依赖
uv lock

# 5. 测试
uv sync
uv run python app.py

# 6. 删除旧文件（可选）
rm requirements.txt  # 或保留备用
```

## CI/CD 配置示例

### GitHub Actions
```yaml
name: Deploy

on: [push]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      
      - name: Sync dependencies
        run: uv sync --no-dev
      
      - name: Run tests
        run: uv run pytest
      
      - name: Deploy
        run: |
          uv run gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 性能对比

| 操作 | pip | uv |
|------|-----|-----|
| 安装依赖 | ~60s | ~3s |
| 创建虚拟环境 | ~5s | ~0.5s |
| 锁定依赖 | ~30s | ~1s |
| 磁盘空间 | ~200MB | ~150MB |

## 注意事项

1. **提交 uv.lock**: 这是 uv 的核心优势，确保环境一致性
2. **.python-version**: 建议指定明确的 Python 版本
3. **分层依赖**: 开发工具放入 `[project.optional-dependencies]`
4. **缓存**: uv 有全局缓存，首次安装后后续极快

## 参考链接

- [uv 官方文档](https://docs.astral.sh/uv/)
- [PEP 621 – Storing project metadata in pyproject.toml](https://peps.python.org/pep-0621/)
- [PEP 517 – A build system independent format for source trees](https://peps.python.org/pep-0517/)
