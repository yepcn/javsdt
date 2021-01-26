# -*- coding:utf-8 -*-
from os import sep, system, walk
from os.path import exists
from shutil import copyfile


# 功能：如果需要为kodi整理头像，则先检查“演员头像for kodi.ini”、“演员头像”文件夹是否存在
# 参数：是否需要整理头像
# 返回：无
# 辅助：os.path.exists，os.system，shutil.copyfile
def check_actors(bool_sculpture):
    if bool_sculpture:
        if not exists('演员头像'):
            print('\n“演员头像”文件夹丢失！请把它放进exe的文件夹中！\n')
            system('pause')
        if not exists('【缺失的演员头像统计For Kodi】.ini'):
            if exists('actors_for_kodi.ini'):
                copyfile('actors_for_kodi.ini', '【缺失的演员头像统计For Kodi】.ini')
                print('\n“【缺失的演员头像统计For Kodi】.ini”成功！')
            else:
                print('\n请打开“【ini】重新创建ini.exe”创建丢失的程序组件!')
                system('pause')


# 功能：检查 归类根目录 是否存在，是不是和视频在同一个磁盘……
# 参数：用户自定义的归类根目录，用户选择整理的文件夹路径
# 返回：归类根目录路径
# 辅助：os.sep，os.system
def check_classify_root(root_custom, root_choose):
    # 用户使用默认的“所选文件夹”
    if root_custom == '所选文件夹':
        return root_choose + sep + '归类完成'
    # 归类根目录 是 用户输入的路径c:\a，继续核实合法性
    else:
        root_custom = root_custom.rstrip(sep)
        # 用户输入的路径 不是 所选文件夹root_choose
        if root_custom != root_choose:
            if root_custom[:2] != root_choose[:2]:
                print('归类的根目录“', root_custom, '”和所选文件夹不在同一磁盘无法归类！请修正！')
                system('pause')
            if not exists(root_custom):
                print('归类的根目录“', root_custom, '”不存在！无法归类！请修正！')
                system('pause')
            return root_custom
        # 用户输入的路径 就是 所选文件夹root_choose
        else:
            return root_choose + sep + '归类完成'


# 功能：所选文件夹总共有多少个视频文件
# 参数：用户选择整理的文件夹路径root_choose，视频类型后缀集合tuple_video_type
# 返回：无
# 辅助：os.walk
def count_num_videos(root_choose, tuple_video_type):
    num_videos = 0
    for root, dirs, files in walk(root_choose):
        for file_raw in files:
            file_temp = file_raw.upper()
            if file_temp.endswith(tuple_video_type) and not file_temp.startswith('.'):
                num_videos += 1
    return num_videos


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
