# -*- coding:utf-8 -*-
from os import sep


# 每一部jav的“结构体”
class JavFile(object):
    def __init__(self, file_raw, root, car, episode, subtitle, num_current):
        self.name = file_raw                                       # 文件名带文件扩展名 ABC-123.mp4
        self.root = root                                           # 视频所在文件夹的路径
        self.car = car                                         # 车牌
        self.episode = episode                                     # 第几集 1 2 3集
        self.subtitle = subtitle                                   # 字幕文件名  ABC-123.srt
        self.type = '.' + file_raw.split('.')[-1].lower()          # 视频文件扩展名 .mp4
        self.subtitle_type = '.' + subtitle.split('.')[-1].lower()     # 字幕扩展名  .srt
        self.number = num_current                                  # 当前处理的视频在所有视频中的编号

    # 视频文件完整路径
    @property
    def path(self):
        return self.root + sep + self.name

    # 视频文件完整路径，但不带文件扩展名
    @property
    def name_no_ext(self):
        return self.name[:-len(self.type)]

    # 所在文件夹名称
    @property
    def folder(self):
        return self.root.split(sep)[-1]

    # 字幕文件完整路径
    @property
    def path_subtitle(self):
        return self.root + sep + self.subtitle