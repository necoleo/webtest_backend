#!/bin/bash
set -e

echo "⏳ 等待数据库就绪..."
# 简单等待几秒，确保数据库连接可用
sleep 3

echo "🔄 执行数据库迁移..."
python manage.py migrate --noinput

echo "📦 收集静态文件..."
python manage.py collectstatic --noinput || true

echo "🚀 启动 Gunicorn..."
exec gunicorn back.wsgi:application -b 0.0.0.0:8000 -w 4 --timeout 120
