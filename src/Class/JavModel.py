from EnumStatus import StatusCompletion, StatusCutType


class JavModel(object):
    def __init__(self, car):
        self.car = car                                     # 车牌

    # 1 通用车牌
    Car = ''
    # 2 原始车牌
    CarOrigin = ''
    # 3 系列
    Series = ''
    # 4 原标题
    Title = ''
    # 5 简体中文标题
    TitleZh = ''
    # 6 剧情概述
    Plot = ''
    # 7 简体剧情
    PlotZh = ''
    # 8 【新】剧评
    Review = ''
    # 9 发行日期
    Release = ''
    # 10 【改】时长
    Runtime = 0
    # 11 导演
    Director = ''
    # 12 制造商
    Studio = ''
    # 13 发行商
    Publisher = ''
    # 14 【新】评分
    Score = 0.0
    # 15 封面Library
    CoverLibrary = ''
    # 16 封面Bus
    CoverBus = ''
    # 17 裁剪方式
    CutType = StatusCutType.Unknown.value
    # 18 db编号
    Javdb = ''
    # 19 library编号
    Javlibrary = ''
    # 20 bus编号
    Javbus = ''
    # 21 arzon编号
    Arzon = ''
    # 22 【新】完成度，三大网站为全部
    Completion = StatusCompletion.only_db.value,
    # 23 【新】版本
    Version = 0,
    # 24 类型
    Genres = []
    # 25 演员们
    Actors = []
