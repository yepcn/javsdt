# -*- coding:utf-8 -*-
import os, re
from shutil import copyfile
from traceback import format_exc
# ################################################# 相同 ###########################################################
from Class.Settings import Settings
from Class.JavFile import JavFile
from EnumStatus import StatusScrape
from Functions.Status import judge_exist_nfo, count_num_videos, judge_separate_folder
from Functions.User import choose_directory
from Functions.Record import record_start, record_fail
from Functions.Process import perfect_dict_data, judge_subtitle_and_divulge
from Functions.Standard import rename_mp4, rename_folder, classify_files, classify_folder
from Functions.XML import replace_xml, replace_xml_win
from Functions.Picture import check_picture, add_watermark_subtitle
from Functions.Requests.Download import download_pic
from Functions.Genre import better_dict_genre
from Functions.Car import list_suren_car
# ################################################## 部分不同 ##########################################################
from Functions.Process import judge_exist_divulge
from Functions.Status import check_actors
from Functions.Standard import collect_sculpture
from Functions.Baidu import translate
from Functions.Picture import add_watermark_divulge, crop_poster_youma
from Functions.Requests.ArzonReq import steal_arzon_cookies, find_plot_arzon
from Functions.Record import record_warn
# ################################################## 独特 ##########################################################
from Functions.Car import find_car_library
from Functions.Requests.JavbusReq import find_series_cover_genres_bus

#  main开始
from JavModel import JavModel
from JavdbReq import find_jav_html_on_db, re_db
from JavlibraryReq import find_jav_html_on_library, re_library

print('1、避开夜晚高峰期，访问javlibrary和arzon很慢。\n'
      '2、若一直打不开javlibrary，请在ini中更新防屏蔽网址\n')

# 读取配置文件，这个ini文件用来给用户设置
print('正在读取ini中的设置...', end='')
try:
    settings = Settings('有码')
except:
    settings = None
    print(format_exc())
    print('\n无法读取ini文件，请修改它为正确格式，或者打开“【ini】重新创建ini.exe”创建全新的ini！')
    os.system('pause')
print('\n读取ini文件成功!\n')

# 路径分隔符: 当前系统的路径分隔符 windows是“\”，linux和mac是“/”
sep = os.sep

# 检查头像: 如果需要为kodi整理头像，先检查演员头像ini、头像文件夹是否存在。
check_actors(settings.bool_sculpture)

# 局部代理: 哪些站点需要代理。
proxy_library, proxy_bus, proxy_321, proxy_db, proxy_arzon, proxy_dmm = settings.get_proxy()

# arzon通行证: 如果需要在nfo中写入日语简介，需要先获得合法的arzon网站的cookie，用于通过成人验证。
cookie_arzon = steal_arzon_cookies(proxy_arzon) if settings.bool_nfo else {}

# jav网址: javlibrary网址 http://www.m45e.com/   javbus网址 https://www.buscdn.work/
url_library = settings.get_url_library()
url_bus = settings.get_url_bus()
url_db = settings.get_url_db()

# 选择简繁中文以及百度翻译账户: 需要简体中文还是繁体中文，影响影片特征和简介。
to_language, tran_id, tran_sk = settings.get_translate_account()

# 信息字典: 存放影片信息，用于给用户自定义各种命名。
dict_for_standard = settings.get_dict_data()

# nfo中title的写法。
list_name_nfo_title = settings.formula_name_nfo_title()
# 额外将哪些元素放入特征中
list_extra_genres = settings.list_extra_genre()
# 重命名视频的格式
list_name_video = settings.formula_rename_video()
# 重命名文件夹的格式
list_name_folder = settings.formula_rename_folder()

# fanart的格式
list_name_fanart = settings.formula_name_fanart()
# poster的格式
list_name_poster = settings.formula_name_poster()

# 视频文件名包含哪些多余的字母数字，需要无视
list_surplus_words_in_filename = settings.list_surplus_word_in_filename()
# 文件名包含哪些特殊含义的文字，判断是否中字
list_subtitle_words_in_filename = settings.list_subtitle_word_in_filename()
# 文件名包含哪些特殊含义的文字，判断是否是无码流出片
list_divulge_words_in_filename = settings.list_divulge_word_in_filename()

# 素人番号: 得到事先设置的素人番号，让程序能跳过它们
list_suren_cars = list_suren_car()

# 需要扫描的文件的类型
tuple_video_types = settings.tuple_video_type()

# 完善dict_data，如果用户自定义了一些文字，不在元素中，需要将它们添加进dict_data；list_classify_basis，归类标准，归类目标文件夹的组成公式。
dict_for_standard, list_classify_basis = perfect_dict_data(list_extra_genres, list_name_video, list_name_folder,
                                                           list_name_nfo_title, list_name_fanart, list_name_poster,
                                                           settings.custom_classify_basis(), dict_for_standard)

# 优化特征的字典
dict_db_genres = better_dict_genre('Javdb', to_language)
dict_library_genres = better_dict_genre('Javlibrary', to_language)
dict_bus_genres = better_dict_genre('Javbus', to_language)

# 是否需要重命名文件夹
bool_rename_folder = settings.judge_need_rename_folder()

# 用户输入“回车”就继续选择文件夹整理
input_start_key = ''
while input_start_key == '':
    # 用户: 选择需要整理的文件夹
    dir_choose = choose_directory()
    # 日志: 在txt中记录一下用户的这次操作，在某个时间选择了某个文件夹
    record_start(dir_choose)
    # 归类: 用户自定义的归类根目录，如果不需要归类则为空
    dir_classify_target = settings.check_classify_target_directory(dir_choose)
    # 计数: 失败次数及进度
    no_fail = 0  # 已经或可能导致致命错误，比如整理未完成，同车牌有不同视频
    no_warn = 0  # 对整理结果不致命的问题，比如找不到简介
    no_current = 0  # 当前视频的编号
    sum_all_videos = count_num_videos(dir_choose, tuple_video_types)  # 所选文件夹总共有多少个视频文件
    print('...文件扫描开始...如果时间过长...请避开高峰期...\n')
    # dir_current【当前所处文件夹】 list_sub_dirs【子文件夹们】 list_sub_files【子文件们】
    for dir_current, list_sub_dirs, list_sub_files in os.walk(dir_choose):
        # 什么文件都没有
        if not list_sub_files:
            continue
        # 当前directory_current是已归类的目录，无需处理
        dir_current_relative = dir_current[len(dir_choose):]  # 当前所处文件夹 相对于 所选文件夹 的路径，用于报错
        if '归类完成' in dir_current_relative:
            continue
        # 跳过已存在nfo的文件夹，判断这一层文件夹中有没有nfo
        if settings.bool_skip and judge_exist_nfo(list_sub_files):
            continue
        # 对这一层文件夹进行评估,有多少视频，有多少同车牌视频，是不是独立文件夹
        list_jav_structs = []  # 存放: 需要整理的jav的结构体
        dict_car_episode = {}  # 存放: 每一车牌的集数， 例如{'abp-123': 1, avop-789': 2}是指 abp-123只有一集，avop-789有cd1、cd2
        dict_subtitle_file = {}  # 存放: jav的字幕文件和车牌对应关系 {'c:\a\abc_123.srt': 'abc-123'}
        # 判断文件是不是字幕文件，放入dict_subtitle_files中
        for file_raw in list_sub_files:
            file_temp = file_raw.upper()
            if file_temp.endswith(('.SRT', '.VTT', '.ASS', '.SSA', '.SUB', '.SMI',)):
                # 当前模式不处理FC2
                if 'FC2' in file_temp:
                    continue
                # 去除用户设置的、干扰车牌的文字
                for word in list_surplus_words_in_filename:
                    file_temp = file_temp.replace(word, '')
                # 得到字幕文件名中的车牌
                subtitle_car = find_car_library(file_temp, list_suren_cars)
                # 将该字幕文件和其中的车牌对应到dict_subtitle_files中
                if subtitle_car:
                    dict_subtitle_file[file_raw] = subtitle_car
        # print(dict_subtitle_files)
        # 判断文件是不是视频，放入list_jav_struct中
        for file_raw in list_sub_files:
            file_temp = file_raw.upper()
            if file_temp.endswith(tuple_video_types) and not file_temp.startswith('.'):
                no_current += 1
                if 'FC2' in file_temp:
                    continue
                for word in list_surplus_words_in_filename:
                    file_temp = file_temp.replace(word, '')
                # 得到视频中的车牌
                car = find_car_library(file_temp, list_suren_cars)
                if car:
                    try:
                        dict_car_episode[car] += 1  # 已经有这个车牌了，加一集cd
                    except KeyError:
                        dict_car_episode[car] = 1  # 这个新车牌有了第一集
                    # 这个车牌在dict_subtitle_files中，有它的字幕。
                    if car in dict_subtitle_file.values():
                        subtitle_file = list(dict_subtitle_file.keys())[list(dict_subtitle_file.values()).index(car)]
                        del dict_subtitle_file[subtitle_file]
                    else:
                        subtitle_file = ''
                    # 将该jav的各种属性打包好，包括原文件名带扩展名、所在文件夹路径、第几集、所属字幕文件名
                    jav_struct = JavFile(file_raw, dir_current, car, dict_car_episode[car], subtitle_file, no_current)
                    list_jav_structs.append(jav_struct)
                else:
                    print(f'>>无法处理: {dir_current_relative}{sep}{file_raw}')

        # 判定影片所在文件夹是否是独立文件夹，独立文件夹是指该文件夹仅用来存放该影片，而不是大杂烩文件夹
        # 这一层文件夹下有jav
        if dict_car_episode:
            bool_separate_folder = judge_separate_folder(len(dict_car_episode), no_current,
                                                         len(list_jav_structs), list_sub_dirs)
        else:
            continue

        # 开始处理每一部jav
        for jav_file in list_jav_structs:

            try:

                # region 准备工作
                path_relative = jav_file.path[len(dir_choose):]  # 影片的相对于所选文件夹的路径，用于报错
                # 当前进度
                print(f'>> [{jav_file.number}/{sum_all_videos}]:{jav_file.name}')
                print(f'    >发现车牌: {jav_file.car}')
                # 是否中字 是否无码流出
                bool_subtitle, bool_divulge = judge_subtitle_and_divulge(jav_file, settings, dict_for_standard, dir_current,
                                                                         list_subtitle_words_in_filename,
                                                                         list_divulge_words_in_filename)
                # endregion

                # region 从javdb获取信息
                status, javdb = find_jav_html_on_db(jav_file, url_db, proxy_db)
                if status == StatusScrape.db_specified_url_wrong:
                    no_fail += 1
                    record_fail(f'    >第{no_fail}个失败！你指定的javdb网址有错误: {path_relative}\n')
                    continue  # 结束对该jav的整理
                elif status == StatusScrape.db_not_found:
                    no_fail += 1
                    record_fail(f'    >第{no_fail}个失败！javdb找不到该车牌的信息: {jav_file.car}，{path_relative}\n')
                    continue  # 结束对该jav的整理
                else:
                    # 成功找到  Status.success
                    pass
                jav_model, genres_db = re_db(url_db, javdb, proxy_db)
                # 优化genres_db
                try:
                    genres_db = [dict_db_genres[i] for i in genres_db if dict_db_genres[i] != '删除']
                except KeyError as error:
                    no_fail += 1
                    record_fail(f'    >第{no_fail}个失败！发现新的javdb特征需要添加至【特征对照表】，另请告知作者: {error}\n')
                    continue  # 结束对该jav的整理
                # endregion

                car = jav_model.car

                # region 从javlibrary获取信息
                status, html_jav_library = find_jav_html_on_library(jav_file, url_library, proxy_library)
                if status == StatusScrape.library_specified_url_wrong:
                    no_fail += 1
                    record_fail(f'    >第{no_fail}个失败！你指定的javlibrary网址有错误: {path_relative}\n')
                    continue  # 结束对该jav的整理
                elif status == StatusScrape.library_not_found:
                    no_fail += 1
                    record_fail(f'    >第{no_fail}个失败！javlibrary找不到该车牌的信息: {jav_file.car}，{path_relative}\n')
                    continue  # 结束对该jav的整理
                elif status == StatusScrape.library_multiple_search_results:
                    bool_unique = False
                    no_fail += 1
                    record_fail(f'    >第{no_fail}个警告！javlibrary搜索到同车牌的不同视频: {jav_file.car}，{path_relative}\n')
                else:
                    # 成功找到  Status.success
                    pass
                # 正则匹配
                genres_library = re_library(jav_model, html_jav_library, settings)
                # 优化genres_library
                try:
                    genres_library = [dict_library_genres[i] for i in genres_library if dict_library_genres[i] != '删除']
                except KeyError as error:
                    no_fail += 1
                    record_fail(f'    >第{no_fail}个失败！发现新的javlibrary特征需要添加至【特征对照表】，另请告知作者: {error}\n')
                    continue  # 结束对该jav的整理
                # print(genres_library)
                # endregion

                # region 前往javbus查找【封面】【系列】【特征】
                status, genres_bus = find_series_cover_genres_bus(jav_model, url_bus, proxy_bus)
                if status == StatusScrape.bus_multiple_search_results:
                    no_warn += 1
                    record_warn(f'    >第{no_warn}个警告！部分信息可能错误，javbus搜索到同车牌的不同视频: {car}，{path_relative}\n')
                if status == StatusScrape.bus_not_found:
                    no_warn += 1
                    record_warn(f'    >第{no_warn}个警告！javbus有码找不到该车牌的信息: {car}，{path_relative}\n')
                # 优化genres_bus
                try:
                    genres_bus = [dict_bus_genres[i] for i in genres_bus
                                  if not i.startswith('AV OP')
                                  or not i.startswith('AVOP')
                                  or dict_bus_genres[i] != '删除']
                except KeyError as error:
                    no_fail += 1
                    record_fail(f'    >失败！发现新的javbus特征需要添加至【特征对照表】，另请告知作者: {error}\n')
                    continue
                # endregion

                # region arzon找简介
                plot_for_nfo = ''
                if jav_file.episode == 1:  # 只有cd1需要，cd2 cd3的nfo写了也没用
                    status, jav_model.Plot, cookie_arzon = find_plot_arzon(car, cookie_arzon, proxy_arzon)
                    if status == StatusScrape.arzon_exist_but_no_plot:
                        no_warn += 1
                        record_warn(f'    >第{no_warn}个失败！找不到简介，尽管arzon上有搜索结果: {path_relative}\n')
                    elif status == StatusScrape.arzon_not_found:
                        no_warn += 1
                        record_warn(f'    >第{no_warn}个失败！找不到简介，影片被arzon下架: {path_relative}\n')
                    elif status == StatusScrape.interrupted:
                        no_warn += 1
                        record_warn(f'    >第{no_warn}个失败！访问arzon失败，需要重新整理该简介: {path_relative}\n')
                    else:
                        # Status.success
                        # 需要翻译简介
                        if settings.bool_tran:
                            plot_for_nfo = translate(tran_id, tran_sk, jav_model.Plot, to_language)
                            if plot_for_nfo.startswith('【百度'):
                                no_fail += 1
                                record_fail(f'    >第{no_fail}个失败！翻译简介失败: {path_relative}\n')
                    # 去除xml文档不允许的特殊字符 &<>
                    plot_for_nfo = replace_xml(plot_for_nfo)
                # print(plot_for_nfo)
                # endregion

                # region 整合完善genres
                genres = list(set(genres_library + genres_bus))
                if bool_subtitle:  # 有“中字“，加上特征”中文字幕”
                    genres.append('中文字幕')
                if bool_divulge:  # 是流出无码片，加上特征'无码流出'
                    genres.append('无码流出')
                # endregion

                ################################################################################
                # 是CD1还是CDn？
                num_all_episodes = dict_car_episode[jav_file.car]  # 该车牌总共多少集
                str_cd = f'-cd{jav_file.episode}' if num_all_episodes > 1 else ''

                # 1重命名视频
                try:
                    dict_for_standard, jav_file, num_temp = rename_mp4(jav_file, no_fail, settings, dict_for_standard, list_name_video,
                                                                       path_relative, str_cd)
                    no_fail = num_temp
                except FileExistsError:
                    no_fail += 1
                    continue

                # 2 归类影片，只针对视频文件和字幕文件。注意: 第2操作和下面（第3操作+第7操作）互斥，只能执行第2操作或（第3操作+第7操作）
                try:
                    jav_file, num_temp = classify_files(jav_file, no_fail, settings, dict_for_standard, list_classify_basis,
                                                        dir_classify_target)
                    no_fail = num_temp
                except FileExistsError:
                    no_fail += 1
                    continue

                # 3重命名文件夹。如果是针对“文件”归类（即第2步），这一步会被跳过，因为用户只需要归类视频文件，不需要管文件夹。
                try:
                    jav_file, num_temp = rename_folder(jav_file, no_fail, bool_rename_folder, dict_for_standard, list_name_folder,
                                                       bool_separate_folder, num_all_episodes)
                    no_fail = num_temp
                except FileExistsError:
                    no_fail += 1
                    continue

                # 更新一下path_relative
                path_relative = f'{sep}{jav_file.path.replace(dir_choose, "")}'  # 影片的相对于所选文件夹的路径，用于报错

                # 4写入nfo【独特】
                if settings.bool_nfo:
                    # 如果是为kodi准备的nfo，不需要多cd
                    if settings.bool_cd_only:
                        path_nfo = f'{jav_file.dir}{sep}{jav_file.name_no_ext.replace(str_cd, "")}.nfo'
                    else:
                        path_nfo = f'{jav_file.dir}{sep}{jav_file.name_no_ext}.nfo'
                    # nfo中tilte的写法
                    title_in_nfo = ''
                    for i in list_name_nfo_title:
                        title_in_nfo += f'{title_in_nfo}{dict_for_standard[i]}'  # nfo中tilte的写法
                    # 开始写入nfo，这nfo格式是参考的kodi的nfo
                    f = open(path_nfo, 'w', encoding="utf-8")
                    f.write(f'<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\" ?>\n'
                            f'<movie>\n'
                            f'  <plot>{jav_model.Plot}{jav_model.Review}</plot>\n'
                            f'  <title>{title_in_nfo}</title>\n'
                            f'  <originaltitle>{jav_model.Car} {jav_model.Title}</originaltitle>\n'
                            f'  <director>{jav_model.Director}</director>\n'
                            f'  <rating>{jav_model.Score}</rating>\n'
                            f'  <criticrating>{str(float(jav_model.Score) * 10)}</criticrating>\n'  # 烂番茄评分 用上面的评分*10
                            f'  <year>{jav_model.Release[0:4]}</year>\n'
                            f'  <mpaa>NC-17</mpaa>\n'
                            f'  <customrating>NC-17</customrating>\n'
                            f'  <countrycode>JP</countrycode>\n'
                            f'  <premiered>{jav_model.Release}</premiered>\n'
                            f'  <release>{jav_model.Release}</release>\n'
                            f'  <runtime>{jav_model.Runtime}</runtime>\n'
                            f'  <country>日本</country>\n'
                            f'  <studio>{jav_model.Studio}</studio>\n'
                            f'  <id>{car}</id>\n'
                            f'  <num>{car}</num>\n'
                            f'  <set>{jav_model.Series}</set>\n')  # emby不管set系列，kodi可以
                    # 需要将特征写入genre
                    if settings.bool_genre:
                        for i in genres:
                            f.write(f'  <genre>{i}</genre>\n')
                        if settings.bool_write_series and jav_model.Series:
                            f.write(f'  <genre>系列:{jav_model.Series}</genre>\n')
                        if settings.bool_write_studio and jav_model.Studio:
                            f.write(f'  <genre>片商:{jav_model.Studio}</genre>\n')
                        if list_extra_genres:
                            for i in list_extra_genres:
                                f.write(f'  <genre>{jav_model.Genres}</genre>\n')
                    # 需要将特征写入tag
                    if settings.bool_tag:
                        for i in genres:
                            f.write(f'  <tag>{i}</tag>\n')
                        if settings.bool_write_series and jav_model.Series:
                            f.write(f'  <tag>系列:{jav_model.Series}</tag>\n')
                        if settings.bool_write_studio and jav_model.Studio:
                            f.write(f'  <tag>片商:{jav_model.Studio}</tag>\n')
                        if list_extra_genres:
                            for i in list_extra_genres:
                                f.write(f'  <tag>{dict_for_standard[i]}</tag>\n')
                    # 写入演员
                    for i in jav_model.Actors:
                        f.write(f'  <actor>\n'
                                f'    <name>{i}</name>\n'
                                f'    <type>Actor</type>\n'
                                f'  </actor>\n')
                    f.write('</movie>\n')
                    f.close()
                    print('    >nfo收集完成')

                # 5需要两张封面图片【独特】
                if settings.bool_jpg:
                    # 下载海报的地址 cover    有一些图片dmm没了，是javlibrary自己的图片，缺少'http:'
                    if not url_cover.startswith('http'):
                        url_cover = f'http:{url_cover}'
                    # url_cover = url_cover.replace('pics.dmm.co.jp', 'jp.netcdn.space')    # 有人建议用avmoo的反代图片地址代替dmm
                    # fanart和poster路径
                    path_fanart = f'{jav_file.dir}{sep}'
                    path_poster = f'{jav_file.dir}{sep}'
                    for i in list_name_fanart:
                        path_fanart += f'{path_fanart}{dict_for_standard[i]}'
                    for i in list_name_poster:
                        path_poster += f'{path_poster}{dict_for_standard[i]}'
                    # kodi只需要一份图片，不管视频是cd几，图片仅一份不需要cd几。
                    if settings.bool_cd_only:
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
                        if bool_unique and settings.bool_bus_first and url_cover_bus and '图书馆' not in jav_file.name:
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
                                    no_fail += 1
                                    record_fail(f'    >第{no_fail}个失败！下载fanart.jpg失败: {url_cover}，{path_relative}\n')
                                    continue  # 【退出对该jav的整理】
                        # 用户没有去javbus获取系列，或者指定“图书馆”网址，还是从javlibrary的dmm图片地址下载
                        else:
                            print('    >从dmm下载封面: ', url_cover)
                            try:
                                download_pic(url_cover, path_fanart, proxy_dmm)
                                print('    >fanart.jpg下载成功')
                            except:
                                no_fail += 1
                                record_fail(f'    >第{no_fail}个失败！下载dmm上的封面失败: {url_cover}，{path_relative}\n')
                                continue  # 【退出对该jav的整理】
                    # 裁剪生成 poster
                    if check_picture(path_poster):
                        # print('    >已有poster.jpg')
                        pass
                    else:
                        crop_poster_youma(path_fanart, path_poster)
                        # 需要加上条纹
                        if settings.bool_watermark_subtitle and bool_subtitle:
                            add_watermark_subtitle(path_poster)
                        if settings.bool_watermark_divulge and bool_divulge:
                            add_watermark_divulge(path_poster)

                # 6收集演员头像【相同】
                if settings.bool_sculpture and jav_file.episode == 1:
                    if jav_model.Actors[0] == '有码演员':
                        print('    >未知演员，无法收集头像')
                    else:
                        collect_sculpture(jav_model.Actors, jav_file.dir)

                # 7归类影片，针对文件夹【相同】
                try:
                    num_temp = classify_folder(jav_file, no_fail, settings, dict_for_standard, list_classify_basis,
                                               dir_classify_target,
                                               dir_current, bool_separate_folder, num_all_episodes)
                    no_fail = num_temp
                except FileExistsError:
                    no_fail += 1
                    continue

            except:
                no_fail += 1
                record_fail(f'    >第{no_fail}个失败！发生错误，如一直在该影片报错请截图并联系作者: {path_relative}\n{format_exc()}\n')
                continue  # 【退出对该jav的整理】

    # 完结撒花
    print('\n当前文件夹完成，', end='')
    if no_fail > 0:
        print('失败', no_fail, '个!  ', dir_choose, '\n')
        line = -1
        with open('【可删除】失败记录.txt', 'r', encoding="utf-8") as f:
            content = list(f)
        while 1:
            if content[line].startswith('已'):
                break
            line -= 1
        for i in range(line + 1, 0):
            print(content[i], end='')
        print('\n“【可删除】失败记录.txt”已记录错误\n')
    else:
        print(' “0”失败！  ', dir_choose, '\n')
    if no_warn > 0:
        print('“警告信息.txt”还记录了', no_warn, '个警告信息！\n')
    # os.system('pause')
    input_start_key = input('回车继续选择文件夹整理: ')
