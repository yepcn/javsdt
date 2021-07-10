# -*- coding:utf-8 -*-
import os
from shutil import copyfile


# 功能：判断当前一级文件夹是否含有nfo文件
# 参数：这层文件夹下的文件们
# 返回：True
# 辅助：无
def judge_exist_nfo(list_files):
    for file in list_files[::-1]:
        if file.endswith('.nfo'):
            return True
    return False


# 功能：判断是否有除了“.actors”"extrafanrt”外的其他文件夹（如果有的话，说明当前文件夹不是jav的独立文件夹）
# 参数：文件夹list
# 返回：True
# 辅助：无
def judge_exist_extra_folders(list_folders):
    for folder in list_folders:
        if folder != '.actors' and folder != 'extrafanart':
            return True
    return False


# 功能：判定影片所在文件夹是否是独立文件夹，独立文件夹是指该文件夹仅用来存放该影片，而不是大杂烩文件夹
# 参数：len_dict_car_pref 当前所处文件夹包含的车牌数量, sum_videos_include(no_current 已是-)当前文件夹中视频的数量，可能有视频不是jav,
#      len_list_jav_struct当前所处文件夹包含的、需要整理的jav的结构体数量, list_sub_dirs当前所处文件夹包含的子文件夹们
# 返回：True
# 辅助：judge_exist_extra_folders
def judge_separate_folder(len_dict_car_pref, sum_videos_include, len_list_jav_struct, list_sub_dirs):
    # 当前文件夹下，车牌不止一个；还有其他非jav视频；有其他文件夹，除了演员头像文件夹“.actors”和额外剧照文件夹“extrafanart”；
    if len_dict_car_pref > 1 or sum_videos_include > len_list_jav_struct or judge_exist_extra_folders(list_sub_dirs):
        return False  # 不是独立的文件夹
    else:
        return True  # 这一层文件夹是这部jav的独立文件夹
