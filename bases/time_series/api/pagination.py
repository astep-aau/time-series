from typing import TypeVar

from fastapi import Query
from fastapi_pagination import Page
from fastapi_pagination.customization import CustomizedPage, UseAdditionalFields, UseName, UseParamsFields

T = TypeVar("T")

DatapointsPage = CustomizedPage[
    Page[T],
    UseName("DatapointsPage"),
    UseParamsFields(size=Query(100, ge=1, le=10000)),
]

RangesPage = CustomizedPage[
    Page[T],
    UseName("RangesPage"),
    UseParamsFields(size=Query(100, ge=1, le=10000)),
    UseAdditionalFields(dataset_id=int),
]
