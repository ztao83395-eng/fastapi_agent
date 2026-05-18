#!/bin/bash
set -e

echo "=== 等待 MySQL 就绪 ==="
for i in $(seq 1 30); do
  if python -c "
import asyncio, os, sys
sys.path.insert(0, '/app')
asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
from sqlalchemy import text
from config.db_conf import async_engine
async def check():
    async with async_engine.connect() as conn:
        await conn.execute(text('SELECT 1'))
asyncio.run(check())
print('OK')
" 2>/dev/null; then
    echo "MySQL 已就绪"
    break
  fi
  echo "等待 MySQL... ($i/30)"
  sleep 2
done

echo "=== 运行集成测试 ==="
cd /app
python -m pytest tests/ -v -s
