"""日志配置：同时写到控制台和文件。

控制台 → docker logs / 终端
文件   → logs/app.log（按 5MB 轮转，保留 3 个备份）
"""

import logging
import logging.handlers
import os
from pathlib import Path

LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))
LOG_FILE = LOG_DIR / "app.log"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 3

_FMT = logging.Formatter(
    "%(asctime)s %(levelname)-7s %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def setup_logging() -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    console = logging.StreamHandler()
    console.setFormatter(_FMT)

    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
    )
    file_handler.setFormatter(_FMT)

    root = logging.getLogger()
    root.setLevel(LOG_LEVEL)
    # --reload 会重复执行模块导入，先清空避免日志打两遍
    for h in root.handlers[:]:
        root.removeHandler(h)
        h.close()
    root.addHandler(console)
    root.addHandler(file_handler)

    # access 日志由中间件负责（带耗时，信息更全），关掉 uvicorn 自带的以免重复
    logging.getLogger("uvicorn.access").disabled = True

    return LOG_FILE
