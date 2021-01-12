# -*- coding:utf-8 -*-
import xlrd


# 功能：得到优化的特征字典
# 参数：用户在用哪个exe（对应sheet_name） ，简繁中文to_language   示例：Javbus有码 ，zh
# 返回：优化的特征字典
# 辅助：xlrd
def better_dict_genre(sheet_name, to_language):
    dict = {}
    # 打开Excel文件
    excel = xlrd.open_workbook('【特征对照表】.xlsx',)
    # 定位excel中的某一sheet
    sheet = excel.sheet_by_name(sheet_name)
    row = sheet.nrows  # 总行数
    for i in range(1, row):
        list_row = sheet.row_values(i)  # i行的list
        if to_language == 'zh':
            dict[list_row[0]] = list_row[1]
        elif to_language == 'cht':
            dict[list_row[0]] = list_row[2]
        else:
            dict[list_row[0]] = list_row[1]
    # print(dict)
    return dict


# print(better_dict_genre('Javlibrary', 'cht'))
