# -*- coding:utf-8 -*-
import re
from os import system


# 功能：发现用于javlibrary的有码车牌，因为T28-、ID比较特殊在
# 参数：大写后的视频文件名file，素人车牌list_suren_car    示例：AVOP-127.MP4    ['LUXU', 'MIUM']
# 返回：发现的车牌    示例：AVOP-127
# 辅助：re.search
def find_car_library(file, list_suren_car):
    # car_pref 车牌前缀 ABP-，带横杠；car_suf，车牌后缀 123。
    # 先处理特例 T28 车牌
    if re.search(r'[^A-Z]?T28[-_ ]*\d\d+', file):
        car_pref = 'T-28'
        car_suf = re.search(r'T28[-_ ]*(\d\d+)', file).group(1)
    # 特例 ID 车牌，在javlibrary上，20ID-020是ID-20020
    elif re.search(r'[^\d]?\d\dID[-_ ]*\d\d+', file):
        carg = re.search(r'[^\d]?(\d\d)ID[-_ ]*(\d\d+)', file)
        car_pref = 'ID-' + carg.group(1)
        car_suf = carg.group(2)
    # 一般车牌
    elif re.search(r'[A-Z][A-Z]+[-_ ]*\d\d+', file):
        carg = re.search(r'([A-Z][A-Z]+)[-_ ]*(\d\d+)', file)
        car_pref = carg.group(1)
        # 如果是素人或无码车牌，不处理
        if car_pref in list_suren_car or car_pref in ['HEYZO', 'PONDO', 'CARIB', 'OKYOHOT']:
            return ''
        car_pref = car_pref + '-'
        car_suf = carg.group(2)
    else:
        return ''
    # 去掉太多的0，AVOP00127 => AVOP-127
    if len(car_suf) > 3:
        car_suf = car_suf[:-3].lstrip('0') + car_suf[-3:]
    return car_pref + car_suf


# 功能：发现原视频文件名中用于javbus的有码车牌
# 参数：大写后的视频文件名，素人车牌list_suren_car    示例：AVOP-127.MP4    ['LUXU', 'MIUM']
# 返回：发现的车牌    示例：AVOP-127
# 辅助：re.search
def find_car_bus(file, list_suren_car):
    # car_pref 车牌前缀 ABP-，带横杠；car_suf，车牌后缀 123。
    # 先处理特例 T28 车牌
    if re.search(r'[^A-Z]?T28[-_ ]*\d\d+', file):
        car_pref = 'T28-'
        car_suf = re.search(r'T28[-_ ]*(\d\d+)', file).group(1)
    # 以javbus上记录的20ID-020为标准
    elif re.search(r'[^\d]?\d\dID[-_ ]*\d\d+', file):
        carg = re.search(r'(\d\d)ID[-_ ]*(\d\d+)', file)
        car_pref = carg.group(1) + 'ID-'
        car_suf = carg.group(2)
    # 一般车牌
    elif re.search(r'[A-Z]+[-_ ]*\d\d+', file):
        carg = re.search(r'([A-Z]+)[-_ ]*(\d\d+)', file)
        car_pref = carg.group(1)
        if car_pref in list_suren_car or car_pref in ['HEYZO', 'PONDO', 'CARIB', 'OKYOHOT']:
            return ''
        car_pref = car_pref + '-'
        car_suf = carg.group(2)
    else:
        return ''
    # 去掉太多的0，avop00127 => avop-127
    if len(car_suf) > 3:
        car_suf = car_suf[:-3].lstrip('0') + car_suf[-3:]
    return car_pref + car_suf


# 功能：发现原视频文件名中的无码车牌
# 参数：被大写后的视频文件名，素人车牌list_suren_car    示例：ABC123ABC123.MP4    ['LUXU', 'MIUM']
# 返回：发现的车牌    示例：ABC123ABC123，只要是字母数字，全拿着
# 辅助：re.search
def find_car_wuma(file, list_suren_car):
    # N12345
    if re.search(r'[^A-Z]?N\d\d+', file):
        car_pref = 'N'
        car_suf = re.search(r'N(\d\d+)', file).group(1)
    # 123-12345
    elif re.search(r'\d+[-_ ]\d\d+', file):
        carg = re.search(r'(\d+)[-_ ](\d\d+)', file)
        car_pref = carg.group(1) + '-'
        car_suf = carg.group(2)
    # 只要是字母数字-_，全拿着
    elif re.search(r'[A-Z0-9]+[-_ ]?[A-Z0-9]+', file):
        carg = re.search(r'([A-Z0-9]+)([-_ ]*)([A-Z0-9]+)', file)
        car_pref = carg.group(1)
        # print(car_pref)
        if car_pref in list_suren_car:
            return ''
        car_pref = car_pref + carg.group(2)
        car_suf = carg.group(3)
    # 下面是处理和一般有码车牌差不多的无码车牌，拿到的往往是错误的，仅在1.0.4版本使用过，宁可不整理也不识别个错的
    # elif search(r'[A-Z]+[-_ ]?\d+', file):
    #     carg = search(r'([A-Z]+)([-_ ]?)(\d+)', file)
    #     car_pref = carg.group(1)
    #     if car_pref in list_suren_car:
    #         return ''
    #     car_pref = car_pref + carg.group(2)
    #     car_suf = carg.group(3)
    else:
        return ''
    # 无码就不去0了，去了0和不去0，可能是不同结果
    # if len(car_suf) > 3:
    #     car_suf = car_suf[:-3].lstrip('0') + car_suf[-3:]
    return car_pref + car_suf


# 功能：发现素人车牌，直接从已记录的list_suren_car中来对比
# 参数：大写后的视频文件名，素人车牌list_suren_car    示例：LUXU-123.MP4    ['LUXU', 'MIUM']
# 返回：发现的车牌    示例：LUXU-123
# 辅助：re.search
def find_car_suren(file, list_suren_car):
    carg = re.search(r'([A-Z][A-Z]+)[-_ ]*(\d\d+)', file)  # 匹配字幕车牌
    if str(carg) != 'None':
        car_pref = carg.group(1)
        # 如果用户把视频文件名指定为jav321上的网址，让该视频通过
        if car_pref not in list_suren_car and '三二一' not in file:
            return ''
        car_suf = carg.group(2)
        # 去掉太多的0，avop00127
        if len(car_suf) > 3:
            car_suf = car_suf[:-3].lstrip('0') + car_suf[-3:]
        return car_pref + '-' + car_suf
    else:
        return ''


# 功能：得到素人车牌集合
# 参数：无
# 返回：素人车牌list
# 辅助：无
def list_suren_car():
    try:
        with open('【素人车牌】.txt', 'r', encoding="utf-8") as f:
            list_suren_cars = list(f)
    except:
        print('【素人车牌】.txt读取失败！停止工作！')
        system('pause')
    list_suren_cars = [i.strip().upper() for i in list_suren_cars if i != '\n']
    # print(list_suren_cars)
    return list_suren_cars
