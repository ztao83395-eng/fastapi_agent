"""图片本地化脚本：下载 picsum.photos 外链图片到 static/images/，并把数据库 URL 改为本地路径。

背景：picsum.photos 为国外 CDN，国内直连经常超时导致图片一直转圈。
本脚本幂等可重复执行：
- 已下载的图片跳过（文件存在且 >500 字节）
- 已本地化的记录跳过（URL 不以 https://picsum.photos 开头）

用法：.venv\\Scripts\\python scripts\\download_images.py
"""
import asyncio
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config.llm_conf  # noqa: F401  触发 .env 加载

from config.redis_conf import redis_client  # noqa: E402
from config.db_conf import AsyncSessionLocal  # noqa: E402
from sqlalchemy import text  # noqa: E402

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "images")
# 下载大尺寸（详情页/列表裁切都清晰）；原 URL 是 200x200
IMAGE_SIZE = "600/400"


def extract_id(url: str) -> str:
    return url.split("/id/")[1].split("/")[0]


def download(url: str):
    """下载单张图片，失败重试 3 次。返回 (id, 状态)"""
    iid = extract_id(url)
    fp = os.path.join(OUT_DIR, f"{iid}.jpg")
    if os.path.exists(fp) and os.path.getsize(fp) > 500:
        return iid, "skip"
    src = f"https://picsum.photos/id/{iid}/{IMAGE_SIZE}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            if len(data) < 500:
                raise ValueError(f"内容异常（{len(data)} 字节）")
            with open(fp, "wb") as f:
                f.write(data)
            return iid, "ok"
        except Exception as e:  # noqa: BLE001  下载失败重试
            if attempt == 2:
                return iid, f"FAIL: {e}"
            time.sleep(1)
    return iid, "FAIL"


async def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    async with AsyncSessionLocal() as db:
        res = await db.execute(
            text("SELECT DISTINCT image FROM news WHERE image IS NOT NULL AND image LIKE 'https://picsum.photos/%'")
        )
        urls = [r[0] for r in res.all()]
    print(f"待处理外链图片: {len(urls)} 个")

    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(download, urls))
    ok = [r for r in results if r[1] in ("ok", "skip")]
    fails = [r for r in results if r[1] != "ok" and r[1] != "skip"]
    print(f"下载完成: 成功/跳过 {len(ok)} 个, 失败 {len(fails)} 个")
    for iid, status in fails:
        print(f"  id={iid} {status}")

    # 数据库 URL 本地化：https://picsum.photos/id/100/200/200 -> /static/images/100.jpg
    async with AsyncSessionLocal() as db:
        preview = await db.execute(text(
            "SELECT id, image, CONCAT('/static/images/', "
            "SUBSTRING_INDEX(SUBSTRING_INDEX(image, '/id/', -1), '/', 1), '.jpg') AS new_image "
            "FROM news WHERE image LIKE 'https://picsum.photos/%' LIMIT 3"
        ))
        print("\n更新预览（前 3 条）:")
        for row in preview.all():
            print(f"  {row.id}: {row.image}  ->  {row.new_image}")

        n = await db.execute(text(
            "UPDATE news SET image = CONCAT('/static/images/', "
            "SUBSTRING_INDEX(SUBSTRING_INDEX(image, '/id/', -1), '/', 1), '.jpg') "
            "WHERE image LIKE 'https://picsum.photos/%'"
        ))
        await db.commit()
        print(f"已更新 {n.rowcount} 条新闻的图片 URL")

    # 清掉带旧 URL 的 Redis 缓存（列表/详情/分类）
    keys = [k async for k in redis_client.scan_iter(match="news_*")]
    if keys:
        await redis_client.delete(*keys)
    await redis_client.delete("news:categories")
    print(f"已清理 Redis 缓存 {len(keys)} 个 key")

    print("\n完成！重启后端后访问 http://localhost:8000/static/images/100.jpg 验证")


asyncio.run(main())
