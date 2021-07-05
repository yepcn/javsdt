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


def jav_model_to_dict_for_user():
    dict_data['车牌'] = car  # car可能发生了变化
    dict_data['车牌前缀'] = car.split('-')[0]
    if premieredg:
        dict_data['发行年月日'] = time_premiered = premieredg.group(1)
        dict_data['发行年份'] = time_premiered[0:4]
        dict_data['月'] = time_premiered[5:7]
        dict_data['日'] = time_premiered[8:10]
    else:
        dict_data['发行年月日'] = '1970-01-01'
        dict_data['发行年份'] = '1970'
        dict_data['月'] = '01'
        dict_data['日'] = '01'
    dict_data['片长'] = runtimeg.group(1) if runtimeg else '0'
    dict_data['导演'] = replace_xml_win(directorg.group(1)) if directorg else '有码导演'
    dict_data['制作商'] = replace_xml_win(studiog.group(1)) if studiog else '有码制作商'
    publisher = publisherg.group(1) if str(publisherg) != 'None' else ''
    #  和 第一个演员
    if actors:
        if len(actors) > 7:
            dict_data['全部演员'] = ' '.join(actors[:7])
        else:
            dict_data['全部演员'] = ' '.join(actors)
        dict_data['首个演员'] = actors[0]
    else:
        dict_data['首个演员'] = dict_data['全部演员'] = '有码演员'
    # 处理影片的标题过长  给用户重命名用的标题是缩减过的，nfo中是“完整标题”，但用户在ini中只用写“标题”
    dict_data['完整标题'] = replace_xml_win(title)
    if len(dict_data['完整标题']) > settings.int_title_len:
        dict_data['标题'] = dict_data['完整标题'][:settings.int_title_len]
    else:
        dict_data['标题'] = dict_data['完整标题']
    # 有些用户需要删去 标题末尾 可能存在的 演员姓名
    if settings.bool_strip_actors and dict_data['标题'] .endswith(dict_data['全部演员']):
        dict_data['标题']  = dict_data['标题'] [:-len(dict_data['全部演员'])].rstrip()
        dict_data['评分'] = '%.1f' % float_score
    else:
        dict_data['评分'] = '0'

    dict_for_user['系列'] = jav_model.Series if jav_model.Series else '有码系列'
    dict_for_user['视频'] = dict_for_user['原文件名'] = jav_file.name_no_ext  # dict_data['视频']，先定义为原文件名，即将发生变化。
    dict_for_user['原文件夹名'] = jav_file.folder
