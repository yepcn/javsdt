# -*- coding:utf-8 -*-
from os.path import splitext, dirname, basename, curdir
from os import sep
from MyEnum import CompletionStatusEnum, CutTypeEnum


# 每一部jav的“结构体”
class JavFile(object):
    def __init__(self, file_raw, dir_current, car, episode, subtitle, num_current):
        self.car = car                                     # 车牌
        self.pref = car.split('-')[0]                      # 车牌前缀
        self.name = file_raw                               # 完整文件名 ABC-123-cd2.mp4；会在重命名过程中发生变化
        self.ext = splitext(file_raw)[1].lower()           # 视频文件扩展名 .mp4
        self.dir = dir_current                             # 视频所在文件夹的路径；会在重命名过程中发生变化
        self.episode = episode                             # 第几集 cd1 cd2 cd3
        self.subtitle = subtitle                           # 字幕文件名  ABC-123.srt；会在重命名过程中发生变化
        self.ext_subtitle = splitext(subtitle)[1].lower()  # 字幕扩展名  .srt
        self.no = num_current                              # 当前处理的视频在所有视频中的编号，整理进度
        self.is_subtitle = False                           # 拥有字幕
        self.is_divulge = False                            # 是无码流出
        self.cd = ''                                       # 多cd，如果有两集，第一集cd1.第二集cd2；如果只有一集，为空

    # 类属性
    is_in_separate_folder = False         # 是否拥有独立文件夹

    # 所在文件夹名称
    @property
    def folder(self):
        return basename(self.dir)

    # 这下面列为属性而不是字段，因为name、dir、subtitle会发生变化
    # 视频文件完整路径
    @property
    def path(self):
        return f'{self.dir}{sep}{self.name}'

    # 视频文件名，但不带文件扩展名
    @property
    def name_no_ext(self):
        return splitext(self.name)[0].lower()

    # 字幕文件完整路径
    @property
    def path_subtitle(self):
        return f'{self.dir}{sep}{self.subtitle}'


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