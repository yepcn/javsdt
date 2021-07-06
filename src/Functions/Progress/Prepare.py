# -*- coding:utf-8 -*-
from os import sep
from os.path import exists
from xml.etree.ElementTree import parse, ParseError


# 功能：完善用于命名的dict_data，如果用户自定义的各种命名公式中有dict_data未包含的元素，则添加进dict_data。
#      将可能比较复杂的list_classify_basis按“+”“\”切割好，准备用于组装后面的归类路径。
# 参数：用户自定义的各种命名公式list
# 返回：存储命名信息的dict_data， 切割好的归类标准list_classify_basis
# 辅助：os.sep
def perfect_dict_data(list_extra_genres, list_rename_video, list_rename_folder, list_name_nfo_title, list_name_fanart, list_name_poster, custom_classify_basis, dict_for_standard):
    for i in list_extra_genres:
        if i not in dict_for_standard:
            dict_for_standard[i] = i
    for i in list_rename_video:
        if i not in dict_for_standard:
            dict_for_standard[i] = i
    for i in list_rename_folder:
        if i not in dict_for_standard:
            dict_for_standard[i] = i
    for i in list_name_nfo_title:
        if i not in dict_for_standard:
            dict_for_standard[i] = i
    for i in list_name_fanart:
        if i not in dict_for_standard:
            dict_for_standard[i] = i
    for i in list_name_poster:
        if i not in dict_for_standard:
            dict_for_standard[i] = i
    list_classify_basis = []
    for i in custom_classify_basis.split('\\'):
        for j in i.split('+'):
            if j not in dict_for_standard:
                dict_for_standard[j] = j
            list_classify_basis.append(j)
        list_classify_basis.append(sep)
    return dict_for_standard, list_classify_basis


# 功能：根据【原文件名】和《已存在的、之前整理的nfo》，判断当前jav是否有“中文字幕”
# 参数：①当前jav所处文件夹路径dir_current ②jav文件名不带格式后缀name_no_ext，
#      ③如果【原文件名】包含list_subtitle_character中的元素即判断有“中文字幕”,
# 返回：True
# 辅助：os.path.exists，xml.etree.ElementTree.parse，xml.etree.ElementTree.ParseError
def judge_exist_subtitle(dir_current, name_no_ext, list_subtitle_character):
    # 去除 '-CD' 和 '-CARIB'对 '-C'判断中字的影响
    name_no_ext = name_no_ext.upper().replace('-CD', '').replace('-CARIB', '')
    # 如果原文件名包含“-c、-C、中字”这些字符
    for i in list_subtitle_character:
        if i in name_no_ext:
            return True
    # 先前整理过的nfo中有 ‘中文字幕’这个Genre
    path_old_nfo = f'{dir_current}{sep}{name_no_ext}.nfo'
    if exists(path_old_nfo):
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
    if exists(path_old_nfo):
        try:
            tree = parse(path_old_nfo)
        except ParseError:  # nfo可能损坏
            return False
        for child in tree.getroot():
            if child.text == '无码流出':
                return True
    return False


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

