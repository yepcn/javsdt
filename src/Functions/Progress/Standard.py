# -*- coding:utf-8 -*-
import os
from os import sep
from configparser import RawConfigParser
from shutil import copyfile
from xml.etree.ElementTree import parse, ParseError


# 功能：根据【原文件名】和《已存在的、之前整理的nfo》，判断当前jav是否有“中文字幕”
# 参数：①当前jav所处文件夹路径dir_current ②jav文件名不带格式后缀name_no_ext，
#      ③如果【原文件名】包含list_subtitle_character中的元素即判断有“中文字幕”,
# 返回：True
# 辅助：os.path.exists，xml.etree.ElementTree.parse，xml.etree.ElementTree.ParseError
from Logger import record_video_old
from MyEnum import StandardStatusEnum
from MyError import TooManyDirectoryLevelsError
from XML import replace_xml_win


def judge_exist_subtitle(dir_current, name_no_ext, list_subtitle_character):
    # 去除 '-CD' 和 '-CARIB'对 '-C'判断中字的影响
    name_no_ext = name_no_ext.upper().replace('-CD', '').replace('-CARIB', '')
    # 如果原文件名包含“-c、-C、中字”这些字符
    for i in list_subtitle_character:
        if i in name_no_ext:
            return True
    # 先前整理过的nfo中有 ‘中文字幕’这个Genre
    path_old_nfo = f'{dir_current}{sep}{name_no_ext}.nfo'
    if os.path.exists(path_old_nfo):
        try:
            tree = parse(path_old_nfo)
        except ParseError:  # nfo可能损坏
            return False
        for child in tree.getroot():
            if child.text == '中文字幕':
                return True
    return False


# 功能：根据【原文件名】和《已存在的、之前整理的nfo》，判断当前jav是否有“无码流出”
# 参数：①当前jav所处文件夹路径dir_current ②jav文件名不带格式后缀name_no_ext，
#      ③如果【原文件名】包含list_divulge_character中的元素即判断有“中文字幕”,
# 返回：True
# 辅助：os.path.exists，xml.etree.ElementTree.parse，xml.etree.ElementTree.ParseError
def judge_exist_divulge(dir_current, name_no_ext, list_divulge_character):
    # 如果原文件名包含“-c、-C、中字”这些字符
    for i in list_divulge_character:
        if i in name_no_ext:
            return True
    # 先前整理过的nfo中有 ‘中文字幕’这个Genre
    path_old_nfo = f'{dir_current}{sep}{name_no_ext}.nfo'
    if os.path.exists(path_old_nfo):
        try:
            tree = parse(path_old_nfo)
        except ParseError:  # nfo可能损坏
            return False
        for child in tree.getroot():
            if child.text == '无码流出':
                return True
    return False


def judge_subtitle_and_divulge(settings, jav_file):
    # 判断是否有中字的特征，条件有三满足其一即可: 1有外挂字幕 2文件名中含有“-C”之类的字眼 3旧的nfo中已经记录了它的中字特征
    if jav_file.subtitle:
        jav_file.is_subtitle = True  # 判定成功
    else:
        jav_file.is_subtitle = judge_exist_subtitle(jav_file.dir_current, jav_file.name_no_ext, settings.list_subtitle_words_in_filename)
    # 判断是否是无码流出的作品，同理
    jav_file.is_divulge = judge_exist_divulge(jav_file.dir_current, jav_file.name_no_ext, settings.list_divulge_words_in_filename)


def prefect_jav_model_and_dict_for_standard(jav_file, jav_model, settings, dict_for_standard):
    # 是否中字 是否无码流出
    judge_subtitle_and_divulge(settings, jav_file)
    # '是否中字'这一命名元素被激活
    dict_for_standard['是否中字'] = settings.custom_subtitle_expression if jav_file.is_subtitle else ''
    dict_for_standard['是否流出'] = settings.custom_divulge_expression if jav_file.is_divulge else ''
    # 车牌
    dict_for_standard['车牌'] = jav_model.Car  # car可能发生了变化
    dict_for_standard['车牌前缀'] = jav_model.Car.split('-')[0]
    # 日期
    dict_for_standard['发行年月日'] = jav_model.Release
    dict_for_standard['发行年份'] = jav_model.Release[0:4]
    dict_for_standard['月'] = jav_model.Release[5:7]
    dict_for_standard['日'] = jav_model.Release[8:10]
    # 演职人员
    dict_for_standard['片长'] = jav_model.Runtime
    dict_for_standard['导演'] = replace_xml_win(jav_model.Director) if jav_model.Director else '有码导演'
    # 公司
    dict_for_standard['发行商'] = replace_xml_win(jav_model.Publisher) if jav_model.Publisher else '有码发行商'
    dict_for_standard['制作商'] = replace_xml_win(jav_model.Studio) if jav_model.Studio else '有码制作商'
    #  和 第一个演员
    if jav_model.Acotrs:
        if len(jav_model.Acotrs) > 7:
            dict_for_standard['全部演员'] = ' '.join(jav_model.Acotrs[:7])
        else:
            dict_for_standard['全部演员'] = ' '.join(jav_model.Acotrs)
        dict_for_standard['首个演员'] = jav_model.Acotrs[0]
    else:
        dict_for_standard['首个演员'] = dict_for_standard['全部演员'] = '有码演员'
    # 处理影片的标题过长  给用户重命名用的标题是缩减过的，nfo中是“完整标题”，但用户在ini中只用写“标题”
    dict_for_standard['完整标题'] = replace_xml_win(jav_model.Title)
    if len(dict_for_standard['完整标题']) > settings.int_title_len:
        dict_for_standard['标题'] = dict_for_standard['完整标题'][:settings.int_title_len]
    else:
        dict_for_standard['标题'] = dict_for_standard['完整标题']
    # 有些用户需要删去 标题末尾 可能存在的 演员姓名
    if settings.bool_strip_actors and dict_for_standard['标题'].endswith(dict_for_standard['全部演员']):
        dict_for_standard['标题'] = dict_for_standard['标题'][:-len(dict_for_standard['全部演员'])].strip()
    dict_for_standard['评分'] = jav_model.Score
    dict_for_standard['系列'] = jav_model.Series if jav_model.Series else '有码系列'
    dict_for_standard['视频'] = dict_for_standard['原文件名'] = jav_file.name_no_ext  # dict_for_standard['视频']，先定义为原文件名，即将发生变化。
    dict_for_standard['原文件夹名'] = jav_file.folder


# 功能：1重命名视频(jav_file和dict_for_standard发生改变）
# 参数：设置settings，命名信息dict_for_standard，处理的影片jav
# 返回：path_return，重命名操作可能因为139行不成功，返回path_return告知主程序提醒用户重新整理
# 辅助：os.exists, os.rename, record_video_old, record_fail
def rename_mp4(jav_file, settings, dict_for_standard):
    # 如果重命名操作不成功，将path_new赋值给path_return，提醒用户自行重命名
    path_return = ''
    if settings.bool_rename_video:
        # 构造新文件名，不带文件类型后缀
        name_without_ext = ''
        for j in settings.list_name_video:
            name_without_ext = f'{name_without_ext}{dict_for_standard[j]}'
        name_without_ext = f'{name_without_ext.strip()}{jav_file.cd}'  # 去除末尾空格，否则windows会自动删除空格，导致程序仍以为带空格
        path_new = f'{jav_file.dir}{sep}{name_without_ext}{jav_file.ext}'  # 【临时变量】path_new 视频文件的新路径
        # 一般情况，不存在同名视频文件
        if not os.path.exists(path_new):
            os.rename(jav_file.path, path_new)
            record_video_old(jav_file.path, path_new)
        # 已存在目标文件，但就是现在的文件
        elif jav_file.path.upper() == path_new.upper():
            try:
                os.rename(jav_file.path, path_new)
            # windows本地磁盘，“abc-123.mp4”重命名为“abc-123.mp4”或“ABC-123.mp4”没问题，但有用户反映，挂载的磁盘会报错“file exists error”
            except:
                # 提醒用户后续自行更改
                path_return = path_new
        # 存在目标文件，不是现在的文件。
        else:
            raise FileExistsError(f'重命名影片失败，重复的影片，已经有相同文件名的视频了：{path_new}')    # 【终止对该jav的整理】
        dict_for_standard['视频'] = name_without_ext      # 【更新】 dict_for_standard['视频']
        jav_file.name = f'{name_without_ext}{jav_file.ext}'   # 【更新】jav.name，重命名操作可能不成功，但之后的操作仍然围绕成功的jav.name来命名
        print(f'    >修改文件名{jav_file.cd}完成')
        # 重命名字幕
        if jav_file.subtitle and settings.bool_rename_subtitle:
            subtitle_new = f'{name_without_ext}{jav_file.ext_subtitle}'   # 【临时变量】subtitle_new
            path_subtitle_new = f'{jav_file.dir}{sep}{subtitle_new}'    # 【临时变量】path_subtitle_new
            if jav_file.path_subtitle != path_subtitle_new:
                os.rename(jav_file.path_subtitle, path_subtitle_new)
                jav_file.subtitle = subtitle_new     # 【更新】 jav.subtitle 字幕完整文件名
            print('    >修改字幕名完成')
    return path_return

# 功能：2归类影片，只针对视频文件和字幕文件，无视它们当前所在文件夹
# 参数：设置settings，归类的目标目录路径dir_classify_target，命名信息dict_for_standard，处理的影片jav
# 返回：处理的影片jav（所在文件夹路径改变）
# 辅助：os.exists, os.rename, os.makedirs，
def classify_files(jav_file, settings, dict_for_standard):
    # 如果需要归类，且不是针对文件夹来归类
    if settings.bool_classify and not settings.bool_classify_folder:
        # 移动的目标文件夹路径
        dir_dest = f'{settings.dir_classify_target}{sep}'
        for j in settings.list_classify_basis:
            dir_dest = f'{dir_dest}{dict_for_standard[j].strip()}'     # 【临时变量】归类的目标文件夹路径    C:\Users\JuneRain\Desktop\测试文件夹\葵司\
        # 还不存在该文件夹，新建
        if not os.path.exists(dir_dest):
            os.makedirs(dir_dest)
        path_new = f'{dir_dest}{sep}{jav_file.name}'      # 【临时变量】新的影片路径
        # 目标文件夹没有相同的影片，防止用户已经有一个“avop-127.mp4”，现在又来一个
        if not os.path.exists(path_new):
            os.rename(jav_file.path, path_new)
            print('    >归类视频文件完成')
            # 移动字幕
            if jav_file.subtitle:
                path_subtitle_new = f'{dir_dest}{sep}{jav_file.subtitle}'  # 【临时变量】新的字幕路径
                if jav_file.path_subtitle != path_subtitle_new:
                    os.rename(jav_file.path_subtitle, path_subtitle_new)
                    # 不再更新 jav.path_subtitle，下面不会再操作 字幕文件
                print('    >归类字幕文件完成')
            jav_file.dir = dir_dest                         # 【更新】jav.dir
        else:
            raise FileExistsError(f'归类失败，重复的影片，归类的目标文件夹已经存在相同的影片: {path_new}')    # 【终止对该jav的整理】


# 功能：3重命名文件夹【相同】如果已进行第2操作，第3操作不会进行，因为用户只需要归类视频文件，不需要管文件夹。
# 参数：重命名文件夹的公式list_name_folder，命名信息dict_for_standard，
#      处理的影片jav，该车牌总共多少cd num_all_episodes
# 返回：处理的影片jav（所在文件夹路径改变）
# 辅助：os.exists, os.rename, os.makedirs，record_fail
def rename_folder(jav_file, dict_for_standard, settings, sum_all_episodes):
    if settings.bool_rename_folder:
        # 构造 新文件夹名folder_new
        folder_new = ''
        for j in settings.list_name_folder:
            folder_new = f'{folder_new}{dict_for_standard[j]}'
        folder_new = folder_new.rstrip(' .')  # 【临时变量】新的所在文件夹。去除末尾空格和“.”
        # 是独立文件夹，才会重命名文件夹
        if jav_file.is_in_separate_folder:
            # 当前视频是该车牌的最后一集，他的兄弟姐妹已经处理完成，才会重命名它们的“家”。
            if jav_file.episode == sum_all_episodes:
                dir_new = f'{os.path.dirname(jav_file.dir)}{sep}{folder_new}'  # 【临时变量】新的影片所在文件夹路径。
                # 想要重命名的目标影片文件夹不存在
                if not os.path.exists(dir_new):
                    os.rename(jav_file.dir, dir_new)
                    jav_file.dir = dir_new            # 【更新】jav.dir
                # 目标影片文件夹存在，但就是现在的文件夹，即新旧相同
                elif jav_file.dir == dir_new:
                    pass
                # 真的有一个同名的文件夹了
                else:
                    raise FileExistsError(f'重命名文件夹失败，已存在相同文件夹：{dir_new}')    # 【终止对该jav的整理】
                print('    >重命名文件夹完成')
        # 不是独立的文件夹，建立独立的文件夹
        else:
            path_separate_folder = f'{jav_file.dir}{sep}{folder_new}'  # 【临时变量】需要创建的的影片所在文件夹。
            # 确认没有同名文件夹
            if not os.path.exists(path_separate_folder):
                os.makedirs(path_separate_folder)
            path_new = f'{path_separate_folder}{sep}{jav_file.name}'   # 【临时变量】新的影片路径
            # 如果这个文件夹是现成的，在它内部确认有没有“abc-123.mp4”。
            if not os.path.exists(path_new):
                os.rename(jav_file.path, path_new)
                # 移动字幕
                if jav_file.subtitle:
                    path_subtitle_new = f'{path_separate_folder}{sep}{jav_file.subtitle}'  # 【临时变量】新的字幕路径
                    os.rename(jav_file.path_subtitle, path_subtitle_new)
                    # 下面不会操作 字幕文件 了，jav.path_subtitle不再更新
                    print('    >移动字幕到独立文件夹')
                jav_file.dir = path_separate_folder                # 【更新】jav.dir
            # 里面已有“avop-127.mp4”，这不是它的家。
            else:
                raise FileExistsError(f'创建独立文件夹失败，已存在相同的视频文件：{path_new}')    # 【终止对该jav的整理】


# 功能：6为当前jav收集演员头像到“.actors”文件夹中
# 参数：演员们 list_actors，jav当前所处文件夹的路径dir_current
# 返回：无
# 辅助：os.path.exists，os.makedirs, configparser.RawConfigParser, shutil.copyfile
def collect_sculpture(list_actors, dir_current):
    for each_actor in list_actors:
        path_exist_actor = f'演员头像{sep}{each_actor[0]}{sep}{each_actor}'  # 事先准备好的演员头像路径
        if os.path.exists(f'{path_exist_actor}.jpg'):
            pic_type = '.jpg'
        elif os.path.exists(f'{path_exist_actor}.png'):
            pic_type = '.png'
        else:
            config_actor = RawConfigParser()
            config_actor.read('【缺失的演员头像统计For Kodi】.ini', encoding='utf-8-sig')
            try:
                each_actor_times = config_actor.get('缺失的演员头像', each_actor)
                config_actor.set("缺失的演员头像", each_actor, str(int(each_actor_times) + 1))
            except:
                config_actor.set("缺失的演员头像", each_actor, '1')
            config_actor.write(open('【缺失的演员头像统计For Kodi】.ini', "w", encoding='utf-8-sig'))
            continue
        # 已经收录了这个演员头像
        dir_dest_actor = f'{dir_current}{sep}.actors{sep}'  # 头像的目标文件夹
        if not os.path.exists(dir_dest_actor):
            os.makedirs(dir_dest_actor)
        # 复制一份到“.actors”
        copyfile(f'{path_exist_actor}{pic_type}', f'{dir_dest_actor}{each_actor}{pic_type}')
        print('    >演员头像收集完成：', each_actor)


# 功能：7归类影片，针对文件夹（如果已进行第2操作，第7操作不会进行，因为用户只需要归类视频文件，不需要管文件夹）
# 参数：设置settings，处理的影片jav，该车牌总共多少cd num_all_episodes，
#      当前处理的文件夹路径dir_current，命名信息dict_for_standard
# 返回：处理的影片jav（所在文件夹路径改变）
# 辅助：os.exists, os.rename, os.makedirs，
def classify_folder(jav_file, settings, dict_for_standard, dir_current, num_all_episodes):
    if settings.bool_classify and settings.bool_classify_folder and jav_file.episode == num_all_episodes:  # 需要移动文件夹，且，是该影片的最后一集
        # 用户选择的文件夹是一部影片的独立文件夹，为了避免在这个文件夹里又生成新的归类文件夹
        if jav_file.is_in_separate_folder and settings.dir_classify_target.startswith(dir_current):
            raise TooManyDirectoryLevelsError(f'无法归类，不建议在当前文件夹【{dir_current}】内再新建归类文件夹，请选择该上级文件夹重新整理: ')
        # 归类放置的目标文件夹
        dir_dest = f'{settings.dir_classify_target}{sep}'
        # 移动的目标文件夹
        for j in settings.list_classify_basis:
            dir_dest = f'{dir_dest}{dict_for_standard[j].rstrip(" .")}'  # 【临时变量】 文件夹移动的目标上级文件夹  C:\Users\JuneRain\Desktop\测试文件夹\1\葵司\
        dir_new = f'{dir_dest}{sep}{jav_file.folder}'  # 【临时变量】 文件夹移动的目标路径   C:\Users\JuneRain\Desktop\测试文件夹\1\葵司\【葵司】AVOP-127\
        # print(dir_new)
        # 还不存在归类的目标文件夹
        if not os.path.exists(dir_new):
            os.makedirs(dir_new)
            # 把现在文件夹里的东西都搬过去
            jav_files = os.listdir(jav_file.dir)
            for i in jav_files:
                os.rename(f'{jav_file.dir}{sep}{i}', f'{dir_new}{sep}{i}')
            # 删除“旧房子”，这是javsdt唯一的删除操作，而且os.rmdir只能删除空文件夹
            os.rmdir(jav_file.dir)
            print('    >归类文件夹完成')
        # 用户已经有了这个文件夹，可能以前处理过同车牌的视频
        else:
            raise FileExistsError(f'归类失败，归类的目标位置已存在相同文件夹：{dir_new}')
