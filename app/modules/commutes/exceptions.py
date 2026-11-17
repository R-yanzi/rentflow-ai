"""通勤业务领域异常。"""

from uuid import UUID


class CommuteBatchError(Exception):
    """批量通勤业务异常基类。"""


class CommuteDestinationNotFoundError(CommuteBatchError):
    """请求的标准目的地点不存在或已停用。"""

    def __init__(
        self,
        destination_location_id: UUID,
    ) -> None:
        self.destination_location_id = destination_location_id

        super().__init__(
            f"Destination location not found: {destination_location_id}",
        )


class CommuteListingsNotFoundError(CommuteBatchError):
    """批量请求中有房源不存在。"""

    def __init__(
        self,
        missing_listing_ids: list[UUID],
    ) -> None:
        # 复制列表，避免调用方后续修改原列表影响异常内容。
        self.missing_listing_ids = list(missing_listing_ids)

        missing_ids = ", ".join(str(listing_id) for listing_id in self.missing_listing_ids)

        super().__init__(
            f"Listings not found: {missing_ids}",
        )
