from MyEnum import CompletionStatusEnum, CutTypeEnum


class JavModel(object):
    def __init__(self, car):
        self.Car = car                # 1 车牌
        self.CarOrigin = ''           # 2 原始车牌
        self.Series = ''              # 3 系列
        self.Title = ''               # 4 原标题
        self.TitleZh = ''             # 5 简体中文标题
        self.Plot = ''                # 6 剧情概述
        self.PlotZh = ''              # 7 简体剧情
        self.Review = ''              # 8 剧评
        self.Release = ''             # 9 发行日期
        self.Runtime = 0              # 10 时长
        self.Director = ''            # 11 导演
        self.Studio = ''              # 12 制造商
        self.Publisher = ''           # 13 发行商
        self.Score = 0.0              # 14 评分
        self.CoverLibrary = ''        # 15 封面Library
        self.CoverBus = ''            # 16 封面Bus
        self.CutType = CutTypeEnum.Unknown.value    # 17 裁剪方式
        self.Javdb = ''               # 18 db编号
        self.Javlibrary = ''          # 19 library编号
        self.Javbus = ''              # 20 bus编号
        self.Arzon = ''               # 21 arzon编号
        self.CompletionStatus = CompletionStatusEnum.only_db.value    # 22 完成度，三大网站为全部
        self.Version = 0              # 23 版本
        self.Genres = []              # 24 类型
        self.Actors = []              # 25 演员们
