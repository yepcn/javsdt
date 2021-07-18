# -*- coding:utf-8 -*-
from os.path import splitext, dirname, basename, curdir
from os import sep


# 每一部jav的“结构体”
class JavFile(object):
    def __init__(self, file_raw, dir_current, car, episode, subtitle, num_current):
        self.car = car                                     # 车牌
        self.pref = car.split('-')[0]                      # 车牌前缀
        self.name = file_raw                               # 完整文件名 ABC-123.mp4；会在重命名过程中发生变化
        self.ext = splitext(file_raw)[1].lower()           # 视频文件扩展名 .mp4
        self.dir = dir_current                             # 视频所在文件夹的路径；会在重命名过程中发生变化
        self.episode = episode                             # 第几集 cd1 cd2 cd3
        self.subtitle = subtitle                           # 字幕文件名  ABC-123.srt；会在重命名过程中发生变化
        self.ext_subtitle = splitext(subtitle)[1].lower()  # 字幕扩展名  .srt
        self.number = num_current                          # 当前处理的视频在所有视频中的编号，整理进度
        self.is_subtitle = False                           # 拥有字幕
        self.is_divulge = False                            # 是无码流出
        self.is_in_separate_folder = False                 # 拥有独立文件夹


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
