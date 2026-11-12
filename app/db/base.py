"""SQLAlchemy ORM 模型的声明基类。"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """所有 ORM 模型共同继承的基类。

    Alembic 后续会读取 Base.metadata，检测模型与数据库之间的差异。
    """
