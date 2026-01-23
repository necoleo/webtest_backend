import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 环境类型：dev / prod
ENV_TYPE = os.environ.get('ENV', 'dev')

# 环境配置文件路径
ENV_FILE_PATH = BASE_DIR / "config" / f".env.{ENV_TYPE}"