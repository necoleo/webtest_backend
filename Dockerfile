# 基础镜像：使用官方 Python 3.9 精简版（与本地开发版本一致）
# slim 版本比完整版小很多，但包含运行 Python 所需的一切
FROM python:3.9-slim

# 设置工作目录
# 后续的 COPY、RUN 等命令都在这个目录下执行
WORKDIR /app

# 设置环境变量
# PYTHONDONTWRITEBYTECODE=1: 不生成 .pyc 字节码文件
# PYTHONUNBUFFERED=1: 不缓冲输出，日志实时显示
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装系统依赖
# default-libmysqlclient-dev: MySQL 客户端库，mysqlclient 包需要
# build-essential: 编译工具，安装某些 Python 包时需要
# pkg-config: 帮助找到已安装的库
# curl: 用于健康检查
# && rm -rf /var/lib/apt/lists/*: 清理 apt 缓存，减小镜像体积
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件
# 单独复制是为了利用 Docker 缓存机制
# 如果 requirements.txt 没变，下次构建会跳过 pip install
COPY requirements.txt .

# 安装 Python 依赖
# --no-cache-dir: 不缓存下载的包，减小镜像体积
# gunicorn: 生产级 WSGI 服务器，比 Django 自带的 runserver 性能好
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# 复制项目代码到容器
# 放在安装依赖之后，这样代码变化时不需要重新安装依赖
COPY . .

# 创建临时文件目录（用于 COS 文件下载）
RUN mkdir -p cos_file_temp

# 声明容器监听的端口（仅作文档说明，不会实际开放端口）
EXPOSE 8000

# 启动命令
# gunicorn: Python WSGI HTTP 服务器
# back.wsgi:application: Django 的 WSGI 入口
# -b 0.0.0.0:8000: 绑定到所有网络接口的 8000 端口
# -w 4: 启动 4 个 worker 进程处理请求
# --timeout 120: 请求超时时间 120 秒
CMD ["gunicorn", "back.wsgi:application", "-b", "0.0.0.0:8000", "-w", "4", "--timeout", "120"]
