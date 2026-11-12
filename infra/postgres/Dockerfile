# 使用官方 PostGIS 镜像作为基础。
# 它基于 PostgreSQL 17，并已经包含 PostGIS。
FROM postgis/postgis:17-3.7

# 安装与 PostgreSQL 17 匹配的 pgvector 扩展。
# --no-install-recommends 避免安装非必要软件。
RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-17-pgvector \
    && rm -rf /var/lib/apt/lists/*