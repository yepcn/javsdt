# -*- coding:utf-8 -*-
from os import sep
import os
from shutil import copyfile
from xml.etree.ElementTree import parse, ParseError



# 功能：如果需要为kodi整理头像，则先检查“演员头像for kodi.ini”、“演员头像”文件夹是否存在; 检查 归类根目录 的合法性
# 参数：是否需要整理头像，用户自定义的归类根目录，用户选择整理的文件夹路径
# 返回：归类根目录路径
# 辅助：os.sep，os.path.exists，shutil.copyfile
def check_actors(self):
    # 检查头像: 如果需要为kodi整理头像，先检查演员头像ini、头像文件夹是否存在。
    if self.bool_sculpture:
        if not os.path.exists('演员头像'):
            input('\n“演员头像”文件夹丢失！请把它放进exe的文件夹中！\n')
        if not os.path.exists('【缺失的演员头像统计For Kodi】.ini'):
            if os.path.exists('actors_for_kodi.ini'):
                copyfile('actors_for_kodi.ini', '【缺失的演员头像统计For Kodi】.ini')
                print('\n“【缺失的演员头像统计For Kodi】.ini”成功！')
            else:
                input('\n请打开“【ini】重新创建ini.exe”创建丢失的程序组件!')


def judge_subtitle_and_divulge(jav_file, settings, dict_for_user, dir_current, list_subtitle_words_in_filename, list_divulge_words_in_filename):
    # 判断是否有中字的特征，条件有三满足其一即可: 1有外挂字幕 2文件名中含有“-C”之类的字眼 3旧的nfo中已经记录了它的中字特征
    if jav_file.subtitle:
        bool_subtitle = True  # 判定成功
        dict_for_user['是否中字'] = settings.custom_subtitle_expression  # '是否中字'这一命名元素被激活
    else:
        bool_subtitle = judge_exist_subtitle(dir_current, jav_file.name_no_ext, list_subtitle_words_in_filename)
        dict_for_user['是否中字'] = settings.custom_subtitle_expression if bool_subtitle else ''
    # 判断是否是无码流出的作品，同理
    bool_divulge = judge_exist_divulge(dir_current, jav_file.name_no_ext, list_divulge_words_in_filename)
    dict_for_user['是否流出'] = settings.custom_divulge_expression if bool_divulge else ''
    return bool_subtitle, bool_divulge


# 功能：得到素人车牌集合
# 参数：无
# 返回：素人车牌list
# 辅助：无
def get_suren_cars():
    try:
        with open('StaticFiles/【素人车牌】.txt', 'r', encoding="utf-8") as f:
            list_suren_cars = list(f)
    except:
        input('【素人车牌】.txt读取失败！')
    list_suren_cars = [i.strip().upper() for i in list_suren_cars if i != '\n']
    # print(list_suren_cars)
    return list_suren_cars

