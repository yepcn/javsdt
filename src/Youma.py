# -*- coding:utf-8 -*-
import os
from shutil import copyfile
from traceback import format_exc
# ################################################# 相同 ###########################################################
from Class.Settings import Settings
from MyEnum import ScrapeStatusEnum
from Class.Logger import Logger
from JavFile import JavFile
from JavModel import JavModel
from Status import judge_exist_nfo, judge_separate_folder
from User import choose_directory
from Standard import rename_mp4, rename_folder, classify_files, classify_folder, prefect_jav_model_and_dict_for_standard
from Picture import check_picture, add_watermark_subtitle
from Download import download_pic
from Genre import better_dict_genre
# ################################################## 部分不同 ##########################################################
from Standard import collect_sculpture
from Picture import add_watermark_divulge, crop_poster_youma
from Functions.Web.Arzon import steal_arzon_cookies, find_plot_arzon
# ################################################## 独特 ##########################################################
from Functions.Web.Javbus import find_series_cover_genres_bus

#  main开始
from Javdb import scrape_from_db
from Javlibrary import scrape_from_library

print('1、避开高峰期，整理速度可能很慢。\n'
      '2、若一直打不开网站，请在ini中更新对应网址\n')

# region（1）读取配置文件
print('正在读取ini中的设置...', end='')
try:
    settings = Settings('有码')
except:
    settings = None
    print(format_exc())
    input('\n无法读取ini文件，请修改它为正确格式，或者打开“【ini】重新创建ini.exe”创建全新的ini！')
print('\n读取ini文件成功!\n')
# endregion

# region（2）准备全局参数
# 路径分隔符: 当前系统的路径分隔符 windows是“\”，linux和mac是“/”
sep = os.sep
# arzon通行证: 如果需要从arzon获取日语简介，需要先获得合法的arzon网站的cookie，用于通过成人验证。
cookie_arzon = steal_arzon_cookies(settings.proxy_arzon) if settings.bool_nfo else {}
# 给用户自定义命名的字典。
dict_for_standard = settings.get_dict_for_standard()
# 优化特征的字典
dict_db_genres = better_dict_genre('Javdb', settings.to_language)
dict_library_genres = better_dict_genre('Javlibrary', settings.to_language)
dict_bus_genres = better_dict_genre('Javbus', settings.to_language)
# endregion

# region（3）整理程序
# 用户输入“回车”就继续选择文件夹整理
input_key = ''
while input_key == '':

    # region （3.1）用户选择需整理的文件夹，校验归类的目标文件夹的合法性
    # 用户: 选择需要整理的文件夹
    dir_choose = choose_directory()
    # 日志: 在txt中记录一下用户的这次操作，在某个时间选择了某个文件夹
    logger = Logger()  # 用于记录失败次数、失败信息
    logger.record_start(dir_choose)
    # 归类: 用户自定义的归类根目录，如果不需要归类则为空
    settings.check_classify_target_directory(dir_choose)
    # endregion

    # region （3.2）遍历所选文件夹内部进行处理
    no_current = 0  # 当前视频（包括非jav）的编号，用于显示进度、获取最大视频编号即当前文件夹内视频数量
    print('...文件扫描开始...如果时间过长...请避开高峰期...\n')
    # dir_current【当前所处文件夹】，由浅及深遍历每一层文件夹，list_sub_dirs【子文件夹们】 list_sub_files【子文件们】
    for dir_current, list_sub_dirs, list_sub_files in os.walk(dir_choose):

        # region （3.2.1）当前文件夹内包含jav及字幕文件的状况：有多少视频，其中多少jav，同一车牌多少cd，当前文件夹是不是独立文件夹
        # （3.2.1.1）当前所处文件夹 相对于 所选文件夹 的路径，主要用于报错
        dir_current_relative = dir_current[len(dir_choose):]
        # 什么文件都没有 | dir_current是已归类的目录，无需处理 | 跳过已存在nfo的文件夹，判断这一层文件夹中有没有nfo
        if not list_sub_files \
                or '归类完成' in dir_current_relative \
                or (settings.bool_skip and judge_exist_nfo(list_sub_files)):
            continue

        # （3.2.1.2）判断文件是不是字幕文件，放入dict_subtitle_file中，字幕文件和车牌对应关系 {'c:\a\abc_123.srt': 'abc-123'}
        dict_subtitle_file = settings.get_dict_subtitle_file(list_sub_files)
        # （3.2.1.3）获取当前所处文件夹，子一级内，包含的jav，放入list_jav_files 存放: 需要整理的jav文件对象jav_file;
        list_jav_files, dict_car_episode, no_current = settings.get_list_jav_files(list_sub_files, no_current,
                                                                                   dict_subtitle_file,
                                                                                   dir_current,
                                                                                   dir_current_relative)
        # dict_car_episode存放: 每一车牌的集数， 例如{'abp-123': 1, avop-789': 2}是指 abp-123只有一集，avop-789有cd1、cd2
        # （3.2.1.4）没有jav，则跳出当前所处文件夹
        if not list_jav_files:
            continue
        # （3.2.1.5）判定当前所处文件夹是否是独立文件夹，独立文件夹是指该文件夹仅用来存放该影片，而不是大杂烩文件夹，是后期移动剪切操作的重要依据
        JavFile.is_in_separate_folder = judge_separate_folder(len(dict_car_episode), no_current,
                                                              len(list_jav_files), list_sub_dirs)
        # is_in_separate_folder是类属性，不是实例属性，修改类属性会将list_jav_files中的所有jav_file的is_in_separate_folder同步
        # （3.2.1.6）所选文件夹总共有多少个视频文件，包括非jav文件，主要用于显示进度
        sum_all_videos = settings.count_num_videos(dir_choose)
        # endregion

        # region（3.2.2）开始处理每一部jav文件
        for jav_file in list_jav_files:
            try:
                # region（3.2.2.1）准备工作
                # 当前进度
                print(f'>> [{jav_file.no}/{sum_all_videos}]:{jav_file.name}')
                print(f'    >发现车牌: {jav_file.car}')
                jav_model = JavModel(jav_file.car)
                logger.path_relative = jav_file.path[len(dir_choose):]  # 影片的相对于所选文件夹的路径，用于报错
                # endregion

                # region（3.2.2.2）从javdb获取信息
                status, genres_db = scrape_from_db(jav_file, jav_model, settings.url_db, settings.proxy_db)
                if status == ScrapeStatusEnum.db_specified_url_wrong:
                    logger.record_fail(f'你指定的javdb网址有错误: ')
                    continue  # 结束对该jav的整理
                elif status == ScrapeStatusEnum.db_not_found:
                    logger.record_fail(f'javdb找不到该车牌的信息: {jav_file.car}，')
                    continue  # 结束对该jav的整理
                # 优化genres_db
                try:
                    genres_db = [dict_db_genres[i] for i in genres_db if dict_db_genres[i] != '删除']
                except KeyError as error:
                    logger.record_fail(f'发现新的javdb特征需要添加至【特征对照表】，另请告知作者: {error}\n')
                    continue  # 结束对该jav的整理
                # endregion

                car = jav_model.Car

                # region（3.2.2.3）从javlibrary获取信息
                status, genres_library = scrape_from_library(jav_file, jav_model, settings.url_library,
                                                             settings.proxy_library)
                if status == ScrapeStatusEnum.library_specified_url_wrong:
                    logger.record_fail(f'你指定的javlibrary网址有错误: ')
                    continue  # 结束对该jav的整理
                elif status == ScrapeStatusEnum.library_not_found:
                    logger.record_fail(f'javlibrary找不到该车牌的信息: {jav_file.car}，')
                    continue  # 结束对该jav的整理
                elif status == ScrapeStatusEnum.library_multiple_search_results:
                    bool_unique = False
                    logger.record_fail(f'javlibrary搜索到同车牌的不同视频: {jav_file.car}，')
                # 优化genres_library
                try:
                    genres_library = [dict_library_genres[i] for i in genres_library if dict_library_genres[i] != '删除']
                except KeyError as error:
                    logger.record_fail(f'发现新的javlibrary特征需要添加至【特征对照表】，另请告知作者: {error}\n')
                    continue  # 结束对该jav的整理
                # endregion

                # region（3.2.2.4）前往javbus查找【封面】【系列】【特征】
                status, genres_bus = find_series_cover_genres_bus(jav_model, settings.url_bus, settings.proxy_bus)
                if status == ScrapeStatusEnum.bus_specified_url_wrong:
                    logger.record_fail(f'你指定的javbus网址有错误: ')
                    continue
                elif status == ScrapeStatusEnum.bus_multiple_search_results:
                    logger.record_warn(f'部分信息可能错误，javbus搜索到同车牌的不同视频: {car}，')
                elif status == ScrapeStatusEnum.bus_not_found:
                    logger.record_warn(f'javbus有码找不到该车牌的信息: {car}，')
                # 优化genres_bus
                try:
                    genres_bus = [dict_bus_genres[i] for i in genres_bus
                                  if not i.startswith('AV OP')
                                  or not i.startswith('AVOP')
                                  or dict_bus_genres[i] != '删除']
                except KeyError as error:
                    logger.record_fail(f'发现新的javbus特征需要添加至【特征对照表】，另请告知作者: {error}\n')
                    continue
                # endregion

                # region（3.2.2.5）arzon找简介
                status, cookie_arzon = find_plot_arzon(jav_model, cookie_arzon, settings.proxy_arzon)
                if status == ScrapeStatusEnum.arzon_exist_but_no_plot:
                    logger.record_warn(f'找不到简介，尽管arzon上有搜索结果: ')
                elif status == ScrapeStatusEnum.arzon_not_found:
                    logger.record_warn(f'找不到简介，影片被arzon下架: ')
                elif status == ScrapeStatusEnum.interrupted:
                    logger.record_warn(f'访问arzon失败，需要重新整理该简介: ')
                # endregion

                # region（3.2.2.6）整合完善genres
                jav_model.Genres = genres = list(set(genres_db + genres_library + genres_bus))
                if jav_file.is_subtitle:  # 有“中字“，加上特征”中文字幕”
                    genres.append('中文字幕')
                if jav_file.is_divulge:  # 是流出无码片，加上特征'无码流出'
                    genres.append('无码流出')
                # endregion

                ################################################################################
                # 是CD1还是CDn？
                sum_all_episodes = dict_car_episode[jav_file.car]  # 该车牌总共多少集
                jav_file.cd = f'-cd{jav_file.episode}' if sum_all_episodes > 1 else ''
                prefect_jav_model_and_dict_for_standard(settings, jav_file, dict_for_standard, jav_model)

                # 1重命名视频
                try:
                    rename_mp4(jav_file, logger, settings, dict_for_standard)
                except FileExistsError:
                    continue

                # 2 归类影片，只针对视频文件和字幕文件。注意: 第2操作和下面（第3操作+第7操作）互斥，只能执行第2操作或（第3操作+第7操作）
                try:
                    classify_files(jav_file, logger, settings, dict_for_standard)
                except FileExistsError:
                    continue

                # 3重命名文件夹。如果是针对“文件”归类（即第2步），这一步会被跳过，因为用户只需要归类视频文件，不需要管文件夹。
                try:
                    rename_folder(jav_file, logger, settings, dict_for_standard, sum_all_episodes)
                except FileExistsError:
                    continue

                # 更新一下path_relative
                logger.path_relative = f'{sep}{jav_file.path.replace(dir_choose, "")}'  # 影片的相对于所选文件夹的路径，用于报错

                # 4写入nfo【独特】
                if settings.bool_nfo:
                    # 如果是为kodi准备的nfo，不需要多cd
                    if settings.bool_cd_only:
                        path_nfo = f'{jav_file.dir}{sep}{jav_file.name_no_ext.replace(jav_file.cd, "")}.nfo'
                    else:
                        path_nfo = f'{jav_file.dir}{sep}{jav_file.name_no_ext}.nfo'
                    # nfo中tilte的写法
                    title_in_nfo = ''
                    for i in settings.list_name_nfo_title:
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
                    for i in settings.list_name_fanart:
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
                    num_temp = classify_folder(jav_file, no_fail, settings, dict_for_standard, dir_classify_target,
                                               dir_current, sum_all_episodes)
                    no_fail = num_temp
                except FileExistsError:
                    no_fail += 1
                    continue

            except:
                logger.record_fail(f'发生错误，如一直在该影片报错请截图并联系作者: {format_exc()}\n')
                continue  # 【退出对该jav的整理】
        # endregion
    # endregion

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
    input_key = input('回车继续选择文件夹整理: ')
# endregion
