from typing import TypeVar

from fastapi import Query
from fastapi_pagination import Page
from fastapi_pagination.customization import CustomizedPage, UseAdditionalFields, UseName, UseParamsFields
from time_series.settings import get_settings

T = TypeVar("T")

DatapointsPage = CustomizedPage[
    Page[T],
    UseName("DatapointsPage"),
    UseParamsFields(size=Query(get_settings().default_page_size, ge=1, le=get_settings().max_page_size)),
]

RangesPage = CustomizedPage[
    Page[T],
    UseName("RangesPage"),
    UseParamsFields(size=Query(get_settings().default_page_size, ge=1, le=get_settings().max_page_size)),
    UseAdditionalFields(dataset_id=int),
]
