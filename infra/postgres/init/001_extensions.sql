-- PostGIS 提供地理空间数据类型、空间索引和距离计算。
CREATE EXTENSION IF NOT EXISTS postgis;

-- pgvector 提供向量数据类型及相似度检索能力。
CREATE EXTENSION IF NOT EXISTS vector;