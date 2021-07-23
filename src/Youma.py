# -*- coding:utf-8 -*-
import os
from traceback import format_exc
from Class.MyHandler import Handler
from Class.MyEnum import ScrapeStatusEnum
from Class.MyLogger import Logger
from Class.MyJav import JavFile, JavModel
from Class.MyError import TooManyDirectoryLevelsError
from Functions.Progress.User import choose_directory
from Functions.Metadata.Genre import better_dict_genres, better_dict_youma_genres
from Functions.Web.Arzon import steal_arzon_cookies, scrape_from_arzon
from Functions.Web.Javbus import scrape_from_bus
from Functions.Web.Javlibrary import scrape_from_library

#  main开始
print('1、避开高峰期，整理速度可能很慢。\n'
      '2、若一直打不开网站，请在ini中更新对应网址\n')

# region（1）读取配置文件
print('正在读取ini中的设置...', end='')
try:
    handler = Handler('有码')
except:
    handler = None
    print(format_exc())
    input('\n无法读取ini文件，请修改它为正确格式，或者打开“【ini】重新创建ini.exe”创建全新的ini！')
print('\n读取ini文件成功!\n')
# endregion

# region（2）准备全局参数
# 路径分隔符: 当前系统的路径分隔符 windows是“\”，linux和mac是“/”
sep = os.sep
# arzon通行证: 如果需要从arzon获取日语简介，需要先获得合法的arzon网站的cookie，用于通过成人验证。
cookie_arzon = steal_arzon_cookies(handler.proxy_arzon) if handler.bool_nfo else {}
# 优化特征的字典
dict_db_genres, dict_library_genres, dict_bus_genres = better_dict_youma_genres(handler.to_language)
# 用于记录失败次数、失败信息
logger = Logger()
# endregion

# region（3）整理程序
# 用户输入“回车”就继续选择文件夹整理
input_key = ''
while not input_key:

    # region （3.1）准备工作，用户选择需整理的文件夹，校验归类的目标文件夹的合法性
    logger.rest()
    handler.rest()
    # 用户选择需要整理的文件夹
    dir_choose = choose_directory()
    # 在txt中记录一下用户的这次操作，在某个时间选择了某个文件夹
    logger.record_start(dir_choose)
    # 若用户需要归类，用户自定义的归类根目录，检查其是否可用
    handler.check_classify_target_directory(dir_choose)
    # endregion

    # region （3.2）遍历所选文件夹内部进行处理
    print('...文件扫描开始...如果时间过长...请避开高峰期...\n')
    # dir_current【当前所处文件夹】，由浅及深遍历每一层文件夹，list_sub_dirs【子文件夹们】 list_sub_files【子文件们】
    for dir_current, list_sub_dirs, list_sub_files in os.walk(dir_choose):
        # region （3.2.1）当前文件夹内包含jav及字幕文件的状况：有多少视频，其中多少jav，同一车牌多少cd，当前文件夹是不是独立文件夹
        # （3.2.1.1）什么文件都没有 | dir_current是已归类的目录，无需处理 | 跳过已存在nfo的文件夹，判断这一层文件夹中有没有nfo
        dir_current_relative = dir_current[len(dir_choose):]    # 当前所处文件夹 相对于 所选文件夹 的路径，主要用于报错
        if not list_sub_files \
                or '归类完成' in dir_current_relative \
                or handler.judge_skip_exist_nfo(list_sub_files):
            continue

        # （3.2.1.2）判断文件是不是字幕文件，放入dict_subtitle_file中，字幕文件和车牌对应关系 {'c:\a\abc_123.srt': 'abc-123'}
        handler.init_dict_subtitle_file(list_sub_files)
        # （3.2.1.3）获取当前所处文件夹，子一级内，包含的jav，放入list_jav_files 存放: 需要整理的jav文件对象jav_file;
        list_jav_files = handler.get_list_jav_files(list_sub_files, dir_current, dir_current_relative)
        # （3.2.1.4）没有jav，则跳出当前所处文件夹
        if not list_jav_files:
            continue
        # （3.2.1.5）判定当前所处文件夹是否是独立文件夹，独立文件夹是指该文件夹仅用来存放该影片，而不是大杂烩文件夹，是后期移动剪切操作的重要依据
        JavFile.is_in_separate_folder = handler.judge_separate_folder(len(list_jav_files), list_sub_dirs)
        # is_in_separate_folder是类属性，不是实例属性，修改类属性会将list_jav_files中的所有jav_file的is_in_separate_folder同步
        # （3.2.1.6）处理“集”的问题，（1）所选文件夹总共有多少个视频文件，包括非jav文件，主要用于显示进度（2）同一车牌有多少cd，用于cd2...命名
        handler.count_num_videos(list_jav_files)
        # endregion

        # region（3.2.2）开始处理每一部jav文件
        for jav_file in list_jav_files:
            try:
                # region（3.2.2.1）准备工作
                # 当前进度
                print(f'>> [{jav_file.no}/{handler.sum_all_videos}]:{jav_file.name}')
                print(f'    >发现车牌: {jav_file.car}')
                jav_model = JavModel(jav_file.car)
                logger.path_relative = jav_file.path[len(dir_choose):]  # 影片的相对于所选文件夹的路径，用于报错
                # endregion

                # region（3.2.2.2）从javdb获取信息
                status, genres_db = scrape_from_db(jav_file, jav_model, handler.url_db, handler.proxy_db)
                if status == ScrapeStatusEnum.db_specified_url_wrong:
                    logger.record_fail(f'你指定的javdb网址有错误: ')
                    continue  # 结束对该jav的整理
                elif status == ScrapeStatusEnum.db_not_found:
                    logger.record_fail(f'javdb找不到该车牌的信息: {jav_file.car}，')
                    continue  # 结束对该jav的整理
                # 优化genres_db
                genres_db = [dict_db_genres[i] for i in genres_db if dict_db_genres[i] != '删除']
                # endregion

                car = jav_model.Car

                # region（3.2.2.3）从javlibrary获取信息
                status, genres_library = scrape_from_library(jav_file, jav_model, handler.url_library,
                                                             handler.proxy_library)
                if status == ScrapeStatusEnum.library_specified_url_wrong:
                    logger.record_fail(f'你指定的javlibrary网址有错误: ')
                    continue  # 结束对该jav的整理
                elif status == ScrapeStatusEnum.library_not_found:
                    logger.record_fail(f'javlibrary找不到该车牌的信息: {jav_file.car}，')
                    continue  # 结束对该jav的整理
                elif status == ScrapeStatusEnum.library_multiple_search_results:
                    logger.record_fail(f'javlibrary搜索到同车牌的不同视频: {jav_file.car}，')
                # 优化genres_library
                genres_library = [dict_library_genres[i] for i in genres_library if dict_library_genres[i] != '删除']
                # endregion

                # region（3.2.2.4）前往javbus查找【封面】【系列】【特征】
                status, genres_bus = scrape_from_bus(jav_file, jav_model, handler.url_bus, handler.proxy_bus)
                if status == ScrapeStatusEnum.bus_specified_url_wrong:
                    logger.record_fail(f'你指定的javbus网址有错误: ')
                    continue
                elif status == ScrapeStatusEnum.bus_multiple_search_results:
                    logger.record_warn(f'部分信息可能错误，javbus搜索到同车牌的不同视频: {car}，')
                elif status == ScrapeStatusEnum.bus_not_found:
                    logger.record_warn(f'javbus有码找不到该车牌的信息: {car}，')
                # 优化genres_bus
                genres_bus = [dict_bus_genres[i] for i in genres_bus
                              if not i.startswith('AV OP')
                              or not i.startswith('AVOP')
                              or dict_bus_genres[i] != '删除']
                # endregion

                # region（3.2.2.5）arzon找简介
                status, cookie_arzon = scrape_from_arzon(jav_model, cookie_arzon, handler.proxy_arzon)
                url_search_arzon = f'https://www.arzon.jp/itemlist.html?t=&m=all&s=&q={car.replace("-", "")}'
                if status == ScrapeStatusEnum.arzon_specified_url_wrong:
                    logger.record_fail(f'你指定的arzon网址有错误: ')
                    continue
                elif status == ScrapeStatusEnum.arzon_exist_but_no_plot:
                    logger.record_warn(f'找不到简介，尽管arzon上有搜索结果: {url_search_arzon}，')
                elif status == ScrapeStatusEnum.arzon_not_found:
                    logger.record_warn(f'找不到简介，影片被arzon下架: {url_search_arzon}，')
                elif status == ScrapeStatusEnum.interrupted:
                    logger.record_warn(f'访问arzon失败，需要重新整理该简介: {url_search_arzon}，')
                # endregion

                # region（3.2.2.6）整合完善genres
                jav_model.Genres = genres = list(set(genres_db + genres_library + genres_bus))
                if jav_file.is_subtitle:  # 有“中字“，加上特征”中文字幕”
                    genres.append('中文字幕')
                if jav_file.is_divulge:  # 是流出无码片，加上特征'无码流出'
                    genres.append('无码流出')
                # endregion

                ################################################################################
                handler.prefect_jav_model_and_dict_for_standard(jav_file, jav_model)

                # 1重命名视频
                path_new = handler.rename_mp4(jav_file)
                if path_new:
                    logger.record_fail(f'请自行重命名大小写：', path_new)

                # 2 归类影片，只针对视频文件和字幕文件。注意: 第2操作和下面（第3操作+第7操作）互斥，只能执行第2操作或（第3操作+第7操作）
                handler.classify_files(jav_file)

                # 3重命名文件夹。如果是针对“文件”归类（即第2步），这一步会被跳过，因为用户只需要归类视频文件，不需要管文件夹。
                handler.rename_folder(jav_file)

                # 更新一下path_relative
                logger.path_relative = f'{sep}{jav_file.path.replace(dir_choose, "")}'  # 影片的相对于所选文件夹的路径，用于报错

                # 4写入nfo【独特】
                handler.write_nfo(jav_file, jav_model, genres)

                # 5需要两张封面图片【独特】
                handler.download_fanart()

                # 6收集演员头像【相同】
                handler.collect_sculpture()

                # 7归类影片，针对文件夹【相同】
                handler.classify_folder(jav_file, dir_current)

            except KeyError as error:
                logger.record_fail(f'发现新的特征需要添加至【特征对照表】，请告知作者: {error}\n')
            except FileExistsError as error:
                logger.record_fail(str(error))
                continue
            except TooManyDirectoryLevelsError as error:
                logger.record_fail(str(error))
                continue
            except:
                logger.record_fail(f'发生错误，如一直在该影片报错请截图并联系作者: {format_exc()}\n')
                continue  # 【退出对该jav的整理】
        # endregion
    # endregion

    # 当前所选文件夹完成
    print('\n当前文件夹完成，', end='')
    logger.print_end(dir_choose)
    input_key = input('回车继续选择文件夹整理: ')
# endregion
