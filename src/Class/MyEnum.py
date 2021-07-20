# -*- coding: UTF-8 -*-
from enum import Enum


class ScrapeStatusEnum(Enum):
    interrupted = 0
    success = 1

    db_specified_url_wrong = 2
    db_multiple_search_results = 3
    db_not_found = 4

    library_specified_url_wrong = 5
    library_multiple_search_results = 6
    library_not_found = 7

    bus_specified_url_wrong = 8
    bus_multiple_search_results = 9
    bus_not_found = 10

    arzon_specified_url_wrong = 11
    arzon_exist_but_no_plot = 12
    arzon_not_found = 13


class CompletionStatusEnum(Enum):
    unknown = 0
    only_db = 1,
    db_library = 2
    db_bus = 3
    db_library_bus = 4


class CutTypeEnum(Enum):
    unknown = 0
    left = 1
    middle = 2
    right = 3
    custom = 4


class MsgTypeEnum(Enum):
    Common = 0
    错误 = 1
    警告 = 2
