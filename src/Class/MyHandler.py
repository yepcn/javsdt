# -*- coding:utf-8 -*-
import os
from os import sep
from configparser import RawConfigParser
from shutil import copyfile
from xml.etree.ElementTree import parse, ParseError


from MyLogger import record_video_old
from MyEnum import StandardStatusEnum
from MyError import TooManyDirectoryLevelsError
from XML import replace_xml_win
from aip import AipBodyAnalysis

# 设置
from Car import find_car_library, find_car_fc2
from MyJav import JavFile


class Handler(object):
    def __init__(self, pattern):
        self._pattern = pattern
        config_settings = RawConfigParser()
        config_settings.read('【点我设置整理规则】.ini', encoding='utf-8-sig')
        ####################################################### nfo ###################################################
        # 是否 跳过已存在nfo的文件夹，不处理已有nfo的文件夹
        self.bool_skip = True if config_settings.get("收集nfo", "是否跳过已存在nfo的文件夹？") == '是' else False
        # 是否 收集nfo
        self.bool_nfo = True if config_settings.get("收集nfo", "是否收集nfo？") == '是' else False
        # 自定义 nfo中title的格式
        self.list_name_nfo_title = config_settings.get("收集nfo", "nfo中title的格式").replace('标题', '完整标题', 1).split('+')
        # 是否 去除 标题 末尾可能存在的演员姓名
        self.bool_strip_actors = True if config_settings.get("收集nfo", "是否去除标题末尾的演员姓名？") == '是' else False
        # 自定义 将系列、片商等元素作为特征，因为emby不会直接在影片介绍页面上显示片商，也不会读取系列set
        self._custom_genres = config_settings.get("收集nfo", "额外将以下元素添加到特征中").split('、') \
            if config_settings.get("收集nfo", "额外将以下元素添加到特征中") else []
        # 自定义 将系列、片商等元素作为特征，因为emby不会直接在影片介绍页面上显示片商，也不会读取系列set
        self._list_extra_genres = [i for i in self._custom_genres if i != '系列' and i != '片商']
        # ？是否将“系列”写入到特征中
        self.bool_write_series = True if '系列' in self._custom_genres else False
        # ？是否将“片商”写入到特征中
        self.bool_write_studio = True if '片商' in self._custom_genres else False
        # 是否 将特征保存到风格中
        self.bool_genre = True if config_settings.get("收集nfo", "是否将特征保存到genre？") == '是' else False
        # 是否 将 片商 作为特征
        self.bool_tag = True if config_settings.get("收集nfo", "是否将特征保存到tag？") == '是' else False
        ####################################################### 重命名 #################################################
        # 是否 重命名 视频
        self.bool_rename_video = True if config_settings.get("重命名影片", "是否重命名影片？") == '是' else False
        # 自定义 重命名 视频
        self._list_rename_video = config_settings.get("重命名影片", "重命名影片的格式").split('+')
        # 是否 重命名视频所在文件夹，或者为它创建独立文件夹
        self._bool_rename_folder = True if config_settings.get("修改文件夹", "是否重命名或创建独立文件夹？") == '是' else False
        # 自定义 新的文件夹名  示例：['车牌', '【', '全部演员', '】']
        self.list_rename_folder = config_settings.get("修改文件夹", "新文件夹的格式").split('+')
        ########################################################## 归类 ################################################
        # 是否 归类jav
        self.bool_classify = True if config_settings.get("归类影片", "是否归类影片？") == '是' else False
        # 是否 针对“文件夹”归类jav，“否”即针对“文件”
        self.bool_classify_folder = True if config_settings.get("归类影片", "针对文件还是文件夹？") == '文件夹' else False
        # 自定义 路径 归类的jav放到哪
        self._custom_classify_target_dir = config_settings.get("归类影片", "归类的根目录")
        # 自定义 jav按什么类别标准来归类 比如：影片类型\全部演员
        self._custom_classify_basis = config_settings.get("归类影片", "归类的标准")
        ######################################################## 图片 ################################################
        # 是否 下载图片
        self.bool_jpg = True if config_settings.get("下载封面", "是否下载封面海报？") == '是' else False
        # 自定义 命名 大封面fanart
        self.list_name_fanart = config_settings.get("下载封面", "DVD封面的格式").split('+')
        # 自定义 命名 小海报poster
        self.list_name_poster = config_settings.get("下载封面", "海报的格式").split('+')
        # 是否 如果视频有“中字”，给poster的左上角加上“中文字幕”的斜杠
        self.bool_watermark_subtitle = True if config_settings.get("下载封面", "是否为海报加上中文字幕条幅？") == '是' else False
        # 是否 如果视频是“无码流出”，给poster的右上角加上“无码流出”的斜杠
        self.bool_watermark_divulge = True if config_settings.get("下载封面", "是否为海报加上无码流出条幅？") == '是' else False
        ###################################################### 字幕 #######################################################
        # 是否 重命名用户已拥有的字幕
        self.bool_rename_subtitle = True if config_settings.get("字幕文件", "是否重命名已有的字幕文件？") == '是' else False
        ###################################################### kodi #######################################################
        # 是否 收集演员头像
        self.bool_sculpture = True if config_settings.get("kodi专用", "是否收集演员头像？") == '是' else False
        # 是否 对于多cd的影片，kodi只需要一份图片和nfo
        self.bool_cd_only = True if config_settings.get("kodi专用", "是否对多cd只收集一份图片和nfo？") == '是' else False
        ###################################################### 代理 ########################################################
        # 代理端口
        self._custom_proxy = config_settings.get("局部代理", "代理端口").strip()
        # 代理，如果为空则效果为不使用
        self._proxys = {'http': f'http://{self._custom_proxy}', 'https': f'https://{self._custom_proxy}'} \
            if config_settings.get("局部代理", "http还是socks5？") == '是' \
            else {'http': f'socks5://{self._custom_proxy}', 'https': f'socks5://{self._custom_proxy}'}
        # 是否 使用局部代理
        self._bool_proxy = True if config_settings.get("局部代理", "是否使用局部代理？") == '是' and self._custom_proxy else False
        # 是否 代理javlibrary
        self.proxy_library = self._proxys if config_settings.get("局部代理", "是否代理javlibrary（有问题）？") == '是' and self._bool_proxy else {}
        # 是否 代理javbus，还有代理javbus上的图片cdnbus
        self.proxy_bus = self._proxys if config_settings.get("局部代理", "是否代理javbus？") == '是' and self._bool_proxy else {}
        # 是否 代理javbus，还有代理javbus上的图片cdnbus
        self.proxy_321 = self._proxys if config_settings.get("局部代理", "是否代理jav321？") == '是' and self._bool_proxy else {}
        # 是否 代理javdb，还有代理javdb上的图片
        self.proxy_db = self._proxys if config_settings.get("局部代理", "是否代理javdb？") == '是' and self._bool_proxy else {}
        # 是否 代理arzon
        self.proxy_arzon = self._proxys if config_settings.get("局部代理", "是否代理arzon？") == '是' and self._bool_proxy else {}
        # 是否 代理dmm图片，javlibrary和javdb上的有码图片几乎都是直接引用dmm
        self.proxy_dmm = self._proxys if config_settings.get("局部代理", "是否代理dmm图片？") == '是' and self._bool_proxy else {}
        #################################################### 原影片文件的性质 ################################################
        # 自定义 无视的字母数字 去除影响搜索结果的字母数字 xhd1080、mm616、FHD-1080
        self._list_surplus_words_in_filename = config_settings.get("原影片文件的性质", "有码素人无视多余的字母数字").upper().split('、') \
            if self._pattern == '有码' \
            else config_settings.get("原影片文件的性质", "无码无视多余的字母数字").upper().split('、')
        # 自定义 原影片性质 影片有中文，体现在视频名称中包含这些字符
        self._list_subtitle_words_in_filename = config_settings.get("原影片文件的性质", "是否中字即文件名包含").strip().split('、')
        # 自定义 是否中字 这个元素的表现形式
        self.custom_subtitle_expression = config_settings.get("原影片文件的性质", "是否中字的表现形式")
        # 自定义 原影片性质 影片是无码流出片，体现在视频名称中包含这些字符
        self._list_divulge_words_in_filename = config_settings.get("原影片文件的性质", "是否流出即文件名包含").strip().split('、')
        # 自定义 是否流出 这个元素的表现形式
        self.custom_divulge_expression = config_settings.get("原影片文件的性质", "是否流出的表现形式")
        # 自定义 原影片性质 有码
        self._av_type = config_settings.get("原影片文件的性质", self._pattern)
        ##################################################### 信息来源 ##################################################
        # 是否 收集javlibrary下方用户超过10个人点赞的评论
        self.bool_review = True if config_settings.get("信息来源", "是否用javlibrary整理影片时收集网友的热评？") == '是' else False
        ################################################### 其他设置 ####################################################
        # 是否 使用简体中文 简介翻译的结果和jav特征会变成“简体”还是“繁体”，影响影片特征和简介。
        self.to_language = 'zh' if config_settings.get("其他设置", "简繁中文？") == '简' else 'cht'
        # 网址 javlibrary
        self.url_library = f'{config_settings.get("其他设置", "javlibrary网址").strip().rstrip("/")}/cn'
        # 网址 javbus
        self.url_bus = config_settings.get("其他设置", "javbus网址").strip().rstrip('/')
        # 网址 javdb
        self.url_db = config_settings.get("其他设置", "javdb网址").strip().rstrip('/')
        # 自定义 文件类型 只有列举出的视频文件类型，才会被处理
        self._tuple_video_types = config_settings.get("其他设置", "扫描文件类型").upper().split('、')
        # 自定义 命名格式中“标题”的长度 windows只允许255字符，所以限制长度，但nfo中的标题是全部
        self.int_title_len = int(config_settings.get("其他设置", "重命名中的标题长度（50~150）"))
        ######################################## 百度翻译API ####################################################
        # 是否 把日语简介翻译为中文
        self.bool_tran = True if config_settings.get("百度翻译API", "是否翻译为中文？") == '是' else False
        # 账户 百度翻译api
        self.tran_id = config_settings.get("百度翻译API", "APP ID")
        self.tran_sk = config_settings.get("百度翻译API", "密钥")
        ######################################## 百度人体分析 ####################################################
        # 是否 需要准确定位人脸的poster
        self.bool_face = True if config_settings.get("百度人体分析", "是否需要准确定位人脸的poster？") == '是' else False
        # 账户 百度人体分析
        self._al_id = config_settings.get("百度人体分析", "appid")
        self._ai_ak = config_settings.get("百度人体分析", "api key")
        self._al_sk = config_settings.get("百度人体分析", "secret key")

        self.dict_for_standard, self.list_classify_basis = self.get_dict_for_standard()
        # 素人番号: 得到事先设置的素人番号，让程序能跳过它们
        self.list_suren_cars = self.get_suren_cars()
        # 是否需要重命名文件夹
        self.bool_rename_folder = self.judge_need_rename_folder()

        self.dir_classify_target = ''
        # 字幕文件和车牌对应关系 {'c:\a\abc_123.srt': 'abc-123'}
        self.dict_subtitle_file = {}
        # 当前视频（包括非jav）的编号，用于显示进度、获取最大视频编号即当前文件夹内视频数量
        self.no_current = 0
        # 存放: 每一车牌的集数， 例如{'abp-123': 1, avop-789': 2}是指 abp-123只有一集，avop-789有cd1、cd2
        self.dict_car_episode = {}
        
        self.sum_all_videos = 0

    def init_dict_and_no(self):
        self.dict_subtitle_file = {}
        self.no_current = 0
        self.dict_car_episode = {}
        self.sum_all_videos = 0

    # #########################[修改文件夹]##############################
    # 是否需要重命名文件夹或者创建新的文件夹
    def judge_need_rename_folder(self):
        if self.bool_classify:  # 如果需要归类
            if self.bool_classify_folder:  # 并且是针对文件夹
                return True  # 那么必须重命名文件夹或者创建新的文件夹
        else:  # 不需要归类
            if self._bool_rename_folder:  # 但是用户本来就在ini中写了要重命名文件夹
                return True
        return False

    # #########################[归类影片]##############################

    # 功能：检查 归类根目录 的合法性
    # 参数：用户自定义的归类根目录，用户选择整理的文件夹路径
    # 返回：归类根目录路径
    # 辅助：os.sep，os.system
    def check_classify_target_directory(self, dir_choose):
        # 检查 归类根目录 的合法性
        if self.bool_classify:
            custom_classify_target_dir = self._custom_classify_target_dir.rstrip(sep)
            # 用户使用默认的“所选文件夹”
            if custom_classify_target_dir == '所选文件夹':
                self.dir_classify_target = f'{dir_choose}{sep}归类完成'
            # 归类根目录 是 用户输入的路径c:\a，继续核实合法性
            else:
                # 用户输入的路径 不是 所选文件夹dir_choose
                if custom_classify_target_dir != dir_choose:
                    if custom_classify_target_dir[:2] != dir_choose[:2]:
                        input(f'归类的根目录：【{custom_classify_target_dir}】和所选文件夹不在同一磁盘无法归类！请修正！')
                    if not os.path.exists(custom_classify_target_dir):
                        input(f'归类的根目录：【{custom_classify_target_dir}】不存在！无法归类！请修正！')
                    self.dir_classify_target = custom_classify_target_dir
                # 用户输入的路径 就是 所选文件夹dir_choose
                else:
                    self.dir_classify_target = f'{dir_choose}{sep}归类完成'
        else:
            self.dir_classify_target = ''

    # #########################[百度人体分析]##############################
    def start_body_analysis(self):
        if self.bool_face:
            return AipBodyAnalysis(self._al_id, self._ai_ak, self._al_sk)
        else:
            return None

    def get_dict_subtitle_file(self, list_sub_files):
        for file_raw in list_sub_files:
            file_temp = file_raw.upper()
            if file_temp.endswith(('.SRT', '.VTT', '.ASS', '.SSA', '.SUB', '.SMI',)):
                if self._pattern != 'Fc2':
                    # 有码无码不处理FC2
                    if 'FC2' in file_temp:
                        continue
                    # 去除用户设置的、干扰车牌的文字
                    for word in self._list_surplus_words_in_filename:
                        file_temp = file_temp.replace(word, '')
                    # 得到字幕文件名中的车牌
                    subtitle_car = find_car_library(file_temp, self.list_suren_cars)
                else:
                    # 仅处理fc2
                    if 'FC2' not in file_temp:
                        continue  # 【跳出2】
                    # 得到字幕文件名中的车牌
                    subtitle_car = find_car_fc2(file_temp)
                # 将该字幕文件和其中的车牌对应到dict_subtitle_file中
                if subtitle_car:
                    self.dict_subtitle_file[file_raw] = subtitle_car


    # dir_current_relative当前所处文件夹 相对于 所选文件夹 的路径，主要用于报错
    def get_list_jav_files(self, list_sub_files, dir_current, dir_current_relative):
        list_jav_files = []  # 存放: 需要整理的jav的结构体
        for file_raw in list_sub_files:
            file_temp = file_raw.upper()
            if file_temp.endswith(self._tuple_video_types) and not file_temp.startswith('.'):
                self.no_current += 1
                if 'FC2' in file_temp:
                    continue
                for word in self._list_surplus_words_in_filename:
                    file_temp = file_temp.replace(word, '')
                # 得到视频中的车牌
                car = find_car_library(file_temp, self.list_suren_cars)
                if car:
                    try:
                        self.dict_car_episode[car] += 1  # 已经有这个车牌了，加一集cd
                    except KeyError:
                        self.dict_car_episode[car] = 1  # 这个新车牌有了第一集
                    # 这个车牌在dict_subtitle_files中，有它的字幕。
                    if car in self.dict_subtitle_file.values():
                        subtitle_file = list(self.dict_subtitle_file.keys())[list(self.dict_subtitle_file.values()).index(car)]
                        del self.dict_subtitle_file[subtitle_file]
                    else:
                        subtitle_file = ''
                    # 将该jav的各种属性打包好，包括原文件名带扩展名、所在文件夹路径、第几集、所属字幕文件名
                    jav_struct = JavFile(file_raw, dir_current, car, self.dict_car_episode[car], subtitle_file, self.no_current)
                    list_jav_files.append(jav_struct)
                else:
                    print(f'>>无法处理: {dir_current_relative}{sep}{file_raw}')
        return list_jav_files

    # 功能：所选文件夹总共有多少个视频文件
    # 参数：用户选择整理的文件夹路径dir_choose
    # 返回：无
    # 辅助：os.walk
    def count_num_videos(self, dir_choose, list_jav_files):
        for dir_current, list_sub_dirs, list_sub_files in os.walk(dir_choose):
            for file_raw in list_sub_files:
                file_temp = file_raw.upper()
                if file_temp.endswith(self._tuple_video_types) and not file_temp.startswith('.'):
                    self.sum_all_videos += 1
        for jav_file in list_jav_files:
            jav_file.sum_all_episodes = self.dict_car_episode[jav_file.car]

    # 功能：完善用于命名的dict_data，如果用户自定义的各种命名公式中有dict_data未包含的元素，则添加进dict_data。
    #      将可能比较复杂的list_classify_basis按“+”“\”切割好，准备用于组装后面的归类路径。
    # 参数：用户自定义的各种命名公式list
    # 返回：存储命名信息的dict_data， 切割好的归类标准list_classify_basis
    # 辅助：os.sep
    def get_dict_for_standard(self):
        if self._pattern == '无码':
            dict_for_standard = {'车牌': 'CBA-123',
                                 '车牌前缀': 'CBA',
                                 '标题': '无码标题',
                                 '完整标题': '完整无码标题',
                                 '导演': '无码导演',
                                 '制作商': '无码制作商',
                                 '发行商': '无码发行商',
                                 '评分': 0.0,
                                 '片长': 0,
                                 '系列': '无码系列',
                                 '发行年月日': '1970-01-01', '发行年份': '1970', '月': '01', '日': '01',
                                 '首个演员': '无码演员', '全部演员': '无码演员',
                                 '空格': ' ',
                                 '\\': sep, '/': sep,  # 文件路径分隔符
                                 '是否中字': '',
                                 '是否流出': '',
                                 '影片类型': self._av_type,  # 自定义有码、无码、素人、FC2的对应称谓
                                 '视频': 'CBA-123',  # 当前及未来的视频文件名，不带ext
                                 '原文件名': 'CBA-123', '原文件夹名': 'CBA-123', }
        elif self._pattern == '素人':
            dict_for_standard = {'车牌': 'XYZ-123',
                                 '车牌前缀': 'XYZ',
                                 '标题': '素人标题',
                                 '完整标题': '完整素人标题',
                                 '导演': '素人导演',
                                 '制作商': '素人制作商',
                                 '发行商': '素人发行商',
                                 '评分': 0.0,
                                 '片长': 0,
                                 '系列': '素人系列',
                                 '发行年月日': '1970-01-01', '发行年份': '1970', '月': '01', '日': '01',
                                 '首个演员': '素人演员', '全部演员': '素人演员',
                                 '空格': ' ',
                                 '\\': sep, '/': sep,  # 文件路径分隔符
                                 '是否中字': '',
                                 '是否流出': '',
                                 '影片类型': self._av_type,  # 自定义有码、无码、素人、FC2的对应称谓
                                 '视频': 'XYZ-123',  # 当前及未来的视频文件名，不带ext
                                 '原文件名': 'XYZ-123', '原文件夹名': 'XYZ-123', }
        elif self._pattern == 'fc2':
            dict_for_standard = {'车牌': 'FC2-123',
                                 '车牌前缀': 'FC2',
                                 '标题': 'FC2标题',
                                 '完整标题': '完整FC2标题',
                                 '导演': 'FC2导演',
                                 '制作商': 'fc2制作商',
                                 '发行商': 'fc2发行商',
                                 '评分': 0.0,
                                 '片长': 0,
                                 '系列': 'FC2系列',
                                 '发行年月日': '1970-01-01', '发行年份': '1970', '月': '01', '日': '01',
                                 '首个演员': 'FC2演员', '全部演员': 'FC2演员',
                                 '空格': ' ',
                                 '\\': sep, '/': sep,  # 文件路径分隔符
                                 '是否中字': '',
                                 '是否流出': '',
                                 '影片类型': self._av_type,  # 自定义有码、无码、素人、FC2的对应称谓
                                 '视频': 'FC2-123',  # 当前及未来的视频文件名，不带ext
                                 '原文件名': 'FC2-123', '原文件夹名': 'FC2-123', }
        else:
            dict_for_standard = {'车牌': 'ABC-123',
                                 '车牌前缀': 'ABC',
                                 '标题': '有码标题',
                                 '完整标题': '完整有码标题',
                                 '导演': '有码导演',
                                 '制作商': '有码制作商',
                                 '发行商': '有码发行商',
                                 '评分': 0.0,
                                 '片长': 0,
                                 '系列': '有码系列',
                                 '发行年月日': '1970-01-01', '发行年份': '1970', '月': '01', '日': '01',
                                 '首个演员': '有码演员', '全部演员': '有码演员',
                                 '空格': ' ',
                                 '\\': sep, '/': sep,  # 文件路径分隔符
                                 '是否中字': '',
                                 '是否流出': '',
                                 '影片类型': self._av_type,  # 自定义有码、无码、素人、FC2的对应称谓
                                 '视频': 'ABC-123',  # 当前及未来的视频文件名，不带ext
                                 '原文件名': 'ABC-123', '原文件夹名': 'ABC-123', }
        for i in self._list_extra_genres:
            if i not in dict_for_standard:
                dict_for_standard[i] = i
        for i in self._list_rename_video:
            if i not in dict_for_standard:
                dict_for_standard[i] = i
        for i in self.list_rename_folder:
            if i not in dict_for_standard:
                dict_for_standard[i] = i
        for i in self.list_name_nfo_title:
            if i not in dict_for_standard:
                dict_for_standard[i] = i
        for i in self.list_name_fanart:
            if i not in dict_for_standard:
                dict_for_standard[i] = i
        for i in self.list_name_poster:
            if i not in dict_for_standard:
                dict_for_standard[i] = i
        list_classify_basis = []
        for i in self._custom_classify_basis.split('\\'):
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
    def judge_exist_subtitle(self, dir_current, name_no_ext, list_subtitle_character):
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

    def judge_subtitle_and_divulge(self, jav_file):
        # 判断是否有中字的特征，条件有三满足其一即可: 1有外挂字幕 2文件名中含有“-C”之类的字眼 3旧的nfo中已经记录了它的中字特征
        if jav_file.subtitle:
            jav_file.is_subtitle = True  # 判定成功
        else:
            jav_file.is_subtitle = self.judge_exist_subtitle(jav_file.dir_current, jav_file.name_no_ext, self.list_subtitle_words_in_filename)
        # 判断是否是无码流出的作品，同理
        jav_file.is_divulge = self.judge_exist_divulge(jav_file.dir_current, jav_file.name_no_ext, self.list_divulge_words_in_filename)

    def prefect_jav_model_and_dict_for_standard(self, jav_file, jav_model, dict_for_standard):
        # 是否中字 是否无码流出
        self.judge_subtitle_and_divulge(jav_file)
        # '是否中字'这一命名元素被激活
        dict_for_standard['是否中字'] = self.custom_subtitle_expression if jav_file.is_subtitle else ''
        dict_for_standard['是否流出'] = self.custom_divulge_expression if jav_file.is_divulge else ''
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
        if len(dict_for_standard['完整标题']) > self.int_title_len:
            dict_for_standard['标题'] = dict_for_standard['完整标题'][:self.int_title_len]
        else:
            dict_for_standard['标题'] = dict_for_standard['完整标题']
        # 有些用户需要删去 标题末尾 可能存在的 演员姓名
        if self.bool_strip_actors and dict_for_standard['标题'].endswith(dict_for_standard['全部演员']):
            dict_for_standard['标题'] = dict_for_standard['标题'][:-len(dict_for_standard['全部演员'])].strip()
        dict_for_standard['评分'] = jav_model.Score
        dict_for_standard['系列'] = jav_model.Series if jav_model.Series else '有码系列'
        dict_for_standard['视频'] = dict_for_standard['原文件名'] = jav_file.name_no_ext  # dict_for_standard['视频']，先定义为原文件名，即将发生变化。
        dict_for_standard['原文件夹名'] = jav_file.folder

    # 功能：1重命名视频(jav_file和dict_for_standard发生改变）
    # 参数：设置settings，命名信息dict_for_standard，处理的影片jav
    # 返回：path_return，重命名操作可能因为139行不成功，返回path_return告知主程序提醒用户重新整理
    # 辅助：os.exists, os.rename, record_video_old, record_fail
    def rename_mp4(self, jav_file, dict_for_standard):
        # 如果重命名操作不成功，将path_new赋值给path_return，提醒用户自行重命名
        path_return = ''
        if self.bool_rename_video:
            # 构造新文件名，不带文件类型后缀
            name_without_ext = ''
            for j in self.list_name_video:
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
            if jav_file.subtitle and self.bool_rename_subtitle:
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
    def classify_files(self, jav_file, dict_for_standard):
        # 如果需要归类，且不是针对文件夹来归类
        if self.bool_classify and not self.bool_classify_folder:
            # 移动的目标文件夹路径
            dir_dest = f'{self.dir_classify_target}{sep}'
            for j in self.list_classify_basis:
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
    # 参数：处理的影片jav
    # 返回：处理的影片jav（所在文件夹路径改变）
    # 辅助：os.exists, os.rename, os.makedirs，record_fail
    def rename_folder(self, jav_file):
        if self.bool_rename_folder:
            # 构造 新文件夹名folder_new
            folder_new = ''
            for j in self.list_name_folder:
                folder_new = f'{folder_new}{self.dict_for_standard[j]}'
            folder_new = folder_new.rstrip(' .')  # 【临时变量】新的所在文件夹。去除末尾空格和“.”
            # 是独立文件夹，才会重命名文件夹
            if jav_file.is_in_separate_folder:
                # 当前视频是该车牌的最后一集，他的兄弟姐妹已经处理完成，才会重命名它们的“家”。
                if jav_file.episode == jav_file.sum_all_episodes:
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
    def collect_sculpture(self, list_actors, dir_current):
        if handler.bool_sculpture and jav_file.episode == 1:
            if jav_model.Actors[0] == '有码演员':
                print('    >未知演员，无法收集头像')
            else:
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
    def classify_folder(self, jav_file, dict_for_standard, dir_current):
        # 需要移动文件夹，且，是该影片的最后一集
        if self.bool_classify and self.bool_classify_folder and jav_file.episode == jav_file.num_all_episodes:
            # 用户选择的文件夹是一部影片的独立文件夹，为了避免在这个文件夹里又生成新的归类文件夹
            if jav_file.is_in_separate_folder and self.dir_classify_target.startswith(dir_current):
                raise TooManyDirectoryLevelsError(f'无法归类，不建议在当前文件夹【{dir_current}】内再新建归类文件夹，请选择该上级文件夹重新整理: ')
            # 归类放置的目标文件夹
            dir_dest = f'{self.dir_classify_target}{sep}'
            # 移动的目标文件夹
            for j in self.list_classify_basis:
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

    # 功能：得到素人车牌集合
    # 参数：无
    # 返回：素人车牌list
    # 辅助：无
    @staticmethod
    def get_suren_cars():
        try:
            with open('StaticFiles/【素人车牌】.txt', 'r', encoding="utf-8") as f:
                list_suren_cars = list(f)
        except:
            input('【素人车牌】.txt读取失败！')
        list_suren_cars = [i.strip().upper() for i in list_suren_cars if i != '\n']
        # print(list_suren_cars)
        return list_suren_cars

    def write_nfo(self, jav_file, jav_model, genres):
        if self.bool_nfo:
            # 如果是为kodi准备的nfo，不需要多cd
            if self.bool_cd_only:
                path_nfo = f'{jav_file.dir}{sep}{jav_file.name_no_ext.replace(jav_file.cd, "")}.nfo'
            else:
                path_nfo = f'{jav_file.dir}{sep}{jav_file.name_no_ext}.nfo'
            # nfo中tilte的写法
            title_in_nfo = ''
            for i in self.list_name_nfo_title:
                title_in_nfo += f'{title_in_nfo}{self.dict_for_standard[i]}'  # nfo中tilte的写法
            # 开始写入nfo，这nfo格式是参考的kodi的nfo
            f = open(path_nfo, 'w', encoding="utf-8")
            f.write(f'<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\" ?>\n'
                    f'<movie>\n'
                    f'  <plot>{jav_model.Plot}{jav_model.Review}</plot>\n'
                    f'  <title>{title_in_nfo}</title>\n'
                    f'  <originaltitle>{jav_model.Car} {jav_model.Title}</originaltitle>\n'
                    f'  <director>{jav_model.Director}</director>\n'
                    f'  <rating>{jav_model.Score}</rating>\n'
                    f'  <criticrating>{float(jav_model.Score) * 10}</criticrating>\n'  # 烂番茄评分 用上面的评分*10
                    f'  <year>{jav_model.Release[0:4]}</year>\n'
                    f'  <mpaa>NC-17</mpaa>\n'
                    f'  <customrating>NC-17</customrating>\n'
                    f'  <countrycode>JP</countrycode>\n'
                    f'  <premiered>{jav_model.Release}</premiered>\n'
                    f'  <release>{jav_model.Release}</release>\n'
                    f'  <runtime>{jav_model.Runtime}</runtime>\n'
                    f'  <country>日本</country>\n'
                    f'  <studio>{jav_model.Studio}</studio>\n'
                    f'  <id>{jav_model.car}</id>\n'
                    f'  <num>{jav_model.car}</num>\n'
                    f'  <set>{jav_model.Series}</set>\n')  # emby不管set系列，kodi可以
            # 需要将特征写入genre
            if self.bool_genre:
                for i in genres:
                    f.write(f'  <genre>{i}</genre>\n')
                if self.bool_write_series and jav_model.Series:
                    f.write(f'  <genre>系列:{jav_model.Series}</genre>\n')
                if self.bool_write_studio and jav_model.Studio:
                    f.write(f'  <genre>片商:{jav_model.Studio}</genre>\n')
                if self.list_extra_genres:
                    for i in self.list_extra_genres:
                        f.write(f'  <genre>{self.dict_for_standard[i]}</genre>\n')
            # 需要将特征写入tag
            if self.bool_tag:
                for i in genres:
                    f.write(f'  <tag>{i}</tag>\n')
                if self.bool_write_series and jav_model.Series:
                    f.write(f'  <tag>系列:{jav_model.Series}</tag>\n')
                if self.bool_write_studio and jav_model.Studio:
                    f.write(f'  <tag>片商:{jav_model.Studio}</tag>\n')
                if self.list_extra_genres:
                    for i in self.list_extra_genres:
                        f.write(f'  <tag>{self.dict_for_standard[i]}</tag>\n')
            # 写入演员
            for i in jav_model.Actors:
                f.write(f'  <actor>\n'
                        f'    <name>{i}</name>\n'
                        f'    <type>Actor</type>\n'
                        f'  </actor>\n')
            f.write('</movie>\n')
            f.close()
            print('    >nfo收集完成')


    def download_fanart(self):
        if handler.bool_jpg:
            # 下载海报的地址 cover    有一些图片dmm没了，是javlibrary自己的图片，缺少'http:'
            if not url_cover.startswith('http'):
                url_cover = f'http:{url_cover}'
            # url_cover = url_cover.replace('pics.dmm.co.jp', 'jp.netcdn.space')    # 有人建议用avmoo的反代图片地址代替dmm
            # fanart和poster路径
            path_fanart = f'{jav_file.dir}{sep}'
            path_poster = f'{jav_file.dir}{sep}'
            for i in handler.list_name_fanart:
                path_fanart += f'{path_fanart}{dict_for_standard[i]}'
            for i in list_name_poster:
                path_poster += f'{path_poster}{dict_for_standard[i]}'
            # kodi只需要一份图片，不管视频是cd几，图片仅一份不需要cd几。
            if handler.bool_cd_only:
                path_fanart = path_fanart.replace(str_cd, '')
                path_poster = path_poster.replace(str_cd, '')
            # emby需要多份，现在不是第一集，直接复制第一集的图片
            elif jav_file.episode != 1:
                try:
                    copyfile(path_fanart.replace(str_cd, '-cd1'), path_fanart)
                    print('    >fanart.jpg复制成功')
                    copyfile(path_poster.replace(str_cd, '-cd1'), path_poster)
                    print('    >poster.jpg复制成功')
                except FileNotFoundError:
                    pass
            # kodi或者emby需要的第一份图片
            if check_picture(path_fanart):
                # print('    >已有fanart.jpg')
                pass
            else:
                # javlibrary上有唯一的搜索结果，优先去取javbus下载封面，已经去过javbus并找到封面，用户没有指定javbus的网址
                if handler.bool_bus_first and url_cover_bus and '图书馆' not in jav_file.name:
                    print('    >从javbus下载封面: ', url_cover_bus)
                    try:
                        download_pic(url_cover_bus, path_fanart, proxy_bus)
                        print('    >fanart.jpg下载成功')
                    except:
                        print('    >从javbus下载fanart.jpg失败!')
                        # 还是用javlibrary的dmm图片
                        print('    >从dmm下载封面: ', url_cover)
                        try:
                            download_pic(url_cover, path_fanart, proxy_dmm)
                            print('    >fanart.jpg下载成功')
                        except:
                            logger.record_fail(f'下载fanart.jpg失败: {url_cover}，')
                            continue  # 【退出对该jav的整理】
                # 用户没有去javbus获取系列，或者指定“图书馆”网址，还是从javlibrary的dmm图片地址下载
                else:
                    print('    >从dmm下载封面: ', url_cover)
                    try:
                        download_pic(url_cover, path_fanart, proxy_dmm)
                        print('    >fanart.jpg下载成功')
                    except:
                        logger.record_fail(f'下载dmm上的封面失败: {url_cover}，')
                        continue  # 【退出对该jav的整理】
            # 裁剪生成 poster
            if check_picture(path_poster):
                # print('    >已有poster.jpg')
                pass
            else:
                crop_poster_youma(path_fanart, path_poster)
                # 需要加上条纹
                if handler.bool_watermark_subtitle and bool_subtitle:
                    add_watermark_subtitle(path_poster)
                if handler.bool_watermark_divulge and bool_divulge:
                    add_watermark_divulge(path_poster)

    # 功能：判断当前一级文件夹是否含有nfo文件
    # 参数：这层文件夹下的文件们
    # 返回：True
    # 辅助：无
    def judge_skip_exist_nfo(self, list_files):
        if self.bool_skip:
            for file in list_files[::-1]:
                if file.endswith('.nfo'):
                    return True
        return False

    # 功能：判定影片所在文件夹是否是独立文件夹，独立文件夹是指该文件夹仅用来存放该影片，不包含“.actors”"extrafanrt”外的其他文件夹
    # 参数：len_dict_car_pref 当前所处文件夹包含的车牌数量, len_list_jav_struct当前所处文件夹包含的、需要整理的jav的结构体数量,
    #      list_sub_dirs当前所处文件夹包含的子文件夹们
    # 返回：True
    # 辅助：judge_exist_extra_folders
    def judge_separate_folder(self, len_list_jav_files, list_sub_dirs):
        # no_current目前是 文件夹中所有视频包括非jav的数量
        sum_videos_include = self.no_current
        # 当前文件夹下，车牌不止一个；还有其他非jav视频；有其他文件夹，除了演员头像文件夹“.actors”和额外剧照文件夹“extrafanart”；
        if len(self.dict_car_episode) > 1 or sum_videos_include > len_list_jav_files:
            return False
        for folder in list_sub_dirs:
            if folder != '.actors' and folder != 'extrafanart':
                return False
        return True  # 这一层文件夹是这部jav的独立文件夹

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
