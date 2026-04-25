#!/bin/bash
# 导出 requirements.txt 用于传统部署

echo "正在导出依赖到 requirements.txt..."

# 使用 uv 导出
uv export --no-dev --format requirements-txt > requirements.txt

echo "导出完成！"
echo ""
echo "文件列表："
ls -la requirements.txt
