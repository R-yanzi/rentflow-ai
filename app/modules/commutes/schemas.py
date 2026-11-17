"""通勤业务输入输出模型。"""

from datetime import datetime

from pydantic import BaseModel

from app.providers.commute.base import CommuteResult


class CommuteCalculation(BaseModel):
    """一次通勤计算及其缓存状态。

    result 是与具体地图厂商无关的标准结果；
    cache_hit 用于日志、监控和后续 API 展示；
    expires_at 表示本结果何时需要重新计算。
    """

    result: CommuteResult
    cache_hit: bool
    expires_at: datetime
