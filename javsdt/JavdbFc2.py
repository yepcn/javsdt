# -*- coding:utf-8 -*-
import os, re
from shutil import copyfile
from traceback import format_exc
########################################################################################################################
from Class.Settings import Settings
from Class.JavFile import JavFile
from Functions.Status import judge_exist_nfo, judge_exist_extra_folders, count_num_videos
from Functions.User import choose_directory
from Functions.Record import record_start, record_fail
from Functions.Process import perfect_dict_data
from Functions.Standard import rename_mp4, rename_folder, classify_files, classify_folder
from Functions.XML import replace_xml_win
from Functions.Process import judge_exist_subtitle
from Functions.Picture import check_picture, add_watermark_subtitle
from Functions.Requests.Download import download_pic
from Functions.Genre import better_dict_genre
# ################################################## 不同 ##########################################################
from Functions.Process import judge_exist_divulge
from Functions.Status import check_actors
from Functions.Picture import add_watermark_divulge, crop_poster_baidu, crop_poster_default
from Functions.Requests.JavdbReq import get_db_html, get_search_db_html


#  main开始
print('1、若一直连不上javdb，请在ini中更新防屏蔽网址\n'
      '2、javdb限制搜索次数，5分钟只能搜索12次左右，然后睡眠5分钟，建议挂机整理！\n'
      '   如果刚启动整理就睡眠，请检查当前网络环境能否访问javdb！\n'
      '4、整理FC2，fc2的信息非常非常少，大概只有个标题、卖家（片商）\n')

# 读取配置文件，这个ini文件用来给用户设置
print('正在读取ini中的设置...', end='')
try:
    settings = Settings('fc2')
except:
    settings = None
    print(format_exc())
    print('\n无法读取ini文件，请修改它为正确格式，或者打开“【ini】重新创建ini.exe”创建全新的ini！')
    os.system('pause')
print('\n读取ini文件成功!\n')


print('进入javdb网站 => 点击主页上的FC2，登录账号 => 键盘按“F12”再按“F5” => 点击“fc2”，复制cfduid和jdb_session')
print('需要看护值守，及时更新它们')
cfduid = input('请粘贴cfduid：')
jdb_session = input('请粘贴jdb_session：')
cookies = {
    "__cfduid": cfduid,
    "_jdb_session": jdb_session,
}

# 路径分隔符：当前系统的路径分隔符 windows是“\”，linux和mac是“/”
sep = os.sep

# 检查头像：如果需要为kodi整理头像，先检查演员头像ini、头像文件夹是否存在。
check_actors(settings.bool_sculpture)

# 局部代理：哪些站点需要代理。
proxy_library, proxy_bus, proxy_321, proxy_db, proxy_arzon, proxy_dmm = settings.get_proxy()

# javdb网址：
url_db = settings.get_url_db()

# 选择简繁中文以及百度翻译账户：需要简体中文还是繁体中文，影响影片特征和简介。
to_language, tran_id, tran_sk = settings.get_translate_account()

# 信息字典：存放影片信息，用于给用户自定义各种命名。
dict_data = {'车牌': 'FC2-123',
             '车牌前缀': 'FC2',
             '标题': 'FC2标题',
             '完整标题': '完整FC2标题',
             '导演': 'FC2导演',
             '片商': 'FC2片商',
             '评分': '0',
             '片长': '0',
             '系列': 'FC2系列',
             '发行年月日': '1970-01-01', '发行年份': '1970', '月': '01', '日': '01',
             '首个演员': 'FC2演员', '全部演员': 'FC2演员',
             '空格': ' ',
             '\\': sep, '/': sep,    # 文件路径分隔符
             '是否中字': '',
             '是否流出': '',
             '影片类型': settings.av_type(),
             '视频': 'FC2-123',    # 当前及未来的视频文件名，不带ext
             '原文件名': 'FC2-123', '原文件夹名': 'FC2-123', }

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
list_surplus_words_in_filename = settings.list_surplus_word_in_filename('有码')
# 文件名包含哪些特殊含义的文字，判断是否中字
list_subtitle_words_in_filename = settings.list_subtitle_word_in_filename()
# 文件名包含哪些特殊含义的文字，判断是否是无码流出片
list_divulge_words_in_filename = settings.list_divulge_word_in_filename()

# 需要扫描的文件的类型
tuple_video_types = settings.tuple_video_type()

# 完善dict_data，如果用户自定义了一些文字，不在元素中，需要将它们添加进dict_data；list_classify_basis，归类标准，归类目标文件夹的组成公式。
dict_data, list_classify_basis= perfect_dict_data(list_extra_genres, list_name_video, list_name_folder, list_name_nfo_title, list_name_fanart, list_name_poster, settings.custom_classify_basis(), dict_data)

# 准备工作：使用人体分析，与百度al建立联系
client = settings.start_body_analysis()

# 优化特征的字典
dict_genre = better_dict_genre('JavdbFc2', to_language)

# 用户输入“回车”就继续选择文件夹整理
input_start_key = ''
while input_start_key == '':
    # 用户：选择需要整理的文件夹
    print('请选择要整理的文件夹：', end='')
    root_choose = choose_directory()
    print(root_choose)
    # 日志：在txt中记录一下用户的这次操作，在某个时间选择了某个文件夹
    record_start(root_choose)
    # 归类：用户自定义的归类根目录，如果不需要归类则为空
    root_classify = settings.check_classify_root(root_choose, sep)
    # 计数：失败次数及进度
    num_fail = 0   # 已经或可能导致致命错误，比如整理未完成，同车牌有不同视频
    num_all_videos = count_num_videos(root_choose, tuple_video_types)    # 所选文件夹总共有多少个视频文件
    num_current = 0    # 当前视频的编号
    print('...文件扫描开始...如果时间过长...请避开夜晚高峰期...\n')
    # root【当前根目录】 dirs【子文件夹】 files【文件】，root是str，后两个是list
    for root, dirs, files in os.walk(root_choose):
        # 什么文件都没有
        if not files:
            continue
        # 当前root是已归类的目录，无需处理
        if '归类完成' in root.replace(root_choose, ''):
            continue
        # 跳过已存在nfo的文件夹，判断这一层文件夹中有没有nfo
        if settings.bool_skip and judge_exist_nfo(files):
            continue
        # 对这一层文件夹进行评估,有多少视频，有多少同车牌视频，是不是独立文件夹
        list_jav_struct = []               # 存放：需要整理的jav的结构体
        dict_car_pref = {}                 # 存放：每一车牌的集数， 例如{'abp-123': 1, avop-789': 2}是指 abp-123只有一集，avop-789有cd1、cd2
        num_videos_include = 0             # 计数：当前文件夹中视频的数量，可能有视频不是jav
        dict_subtitle_files = {}               # 存放：jav的字幕文件和车牌对应关系 {'c:\a\abc_123.srt': 'abc-123'}
        # 判断文件是不是字幕文件，放入dict_subtitle_files中
        for file_raw in files:
            file_temp = file_raw.upper()
            if file_temp.endswith(('.SRT', '.VTT', '.ASS', '.SSA', '.SUB', '.SMI',)):
                # 仅处理fc2
                if 'FC2' not in file_temp:
                    continue    # 【跳出2】
                subtitle_carg = re.search(r'FC2[^\d]*(\d+)', file_temp)  # 匹配字幕车牌
                if str(subtitle_carg) != 'None':
                    subtitle_car = 'FC2-' + subtitle_carg.group(1)
                    dict_subtitle_files[file_raw] = subtitle_car
        # print(dict_subtitle_files)
        # 判断文件是不是视频，放入list_jav_struct中
        for file_raw in files:
            file_temp = file_raw.upper()
            if file_temp.endswith(tuple_video_types) and not file_temp.startswith('.'):
                num_videos_include += 1
                num_current += 1
                # 仅处理fc2
                if 'FC2' not in file_temp:
                    # print('>>无法处理：' + root.replace(root_choose, '') + sep + file_raw)
                    continue  # 【跳出2】
                video_numg = re.search(r'FC2[^\d]*(\d+)', file_temp)  # 匹配视频车牌
                if str(video_numg) != 'None':
                    car = 'FC2-' + video_numg.group(1)
                    # 这个车牌有几集？
                    try:
                        dict_car_pref[car] += 1  # 已经有这个车牌了，加一集cd
                    except KeyError:
                        dict_car_pref[car] = 1  # 这个新车牌有了第一集
                    # 这个车牌在dict_subtitle_files中，有它的字幕。
                    if car in dict_subtitle_files.values():
                        subtitle_file = list(dict_subtitle_files.keys())[list(dict_subtitle_files.values()).index(car)]
                        del dict_subtitle_files[subtitle_file]
                    else:
                        subtitle_file = ''
                    # 将该jav的各种属性打包好，包括原文件名带扩展名、所在文件夹路径、第几集、所属字幕文件名
                    jav_struct = JavFile(file_raw, root, car, dict_car_pref[car], subtitle_file, num_current)
                    list_jav_struct.append(jav_struct)
                else:
                    print('>>无法处理：', root.replace(root_choose, '') + sep + file_raw)

        # 判定影片所在文件夹是否是独立文件夹，独立文件夹是指该文件夹仅用来存放该影片，而不是大杂烩文件夹
        # 这一层文件夹下有jav
        if dict_car_pref:
            # 当前文件夹下，车牌不止一个；还有其他非jav视频；有其他文件夹，除了演员头像文件夹“.actors”和额外剧照文件夹“extrafanart”；
            if len(dict_car_pref) > 1 or num_videos_include > len(list_jav_struct) or judge_exist_extra_folders(dirs):
                bool_separate_folder = False   # 不是独立的文件夹
            else:
                bool_separate_folder = True    # 这一层文件夹是这部jav的独立文件夹
        else:
            continue

        # 开始处理每一部jav
        for jav in list_jav_struct:
            # 告诉用户进度
            print('>> [' + str(jav.number) + '/' + str(num_all_videos) + ']:', jav.name)
            print('    >发现车牌：', jav.car)

            # 判断是否有中字的特征，条件有三满足其一即可：1有外挂字幕 2文件名中含有“-C”之类的字眼 3旧的nfo中已经记录了它的中字特征
            if jav.subtitle:
                bool_subtitle = True    # 判定成功
                dict_data['是否中字'] = settings.custom_subtitle_expression    # '是否中字'这一命名元素被激活
            else:
                bool_subtitle = judge_exist_subtitle(root, jav.name_no_ext, list_subtitle_words_in_filename)
                dict_data['是否中字'] = settings.custom_subtitle_expression if bool_subtitle else ''
            # 判断是否是无码流出的作品，同理
            bool_divulge = judge_exist_divulge(root, jav.name_no_ext, list_divulge_words_in_filename)
            dict_data['是否流出'] = settings.custom_divulge_expression if bool_divulge else ''

            # 影片的相对于所选文件夹的路径，用于报错
            path_relative = sep + jav.path.replace(root_choose, '')

            # 获取nfo信息的javdb网页
            try:
                # 用户指定了网址，则直接得到jav所在网址
                if '图书馆' in jav.name:
                    url_appointg = re.search(r'仓库(.+?)\.', jav.name)
                    if str(url_appointg) != 'None':
                        url_on_web = url_db + 'v/' + url_appointg.group(1)
                    else:
                        num_fail += 1
                        record_fail('    >第' + str(num_fail) + '个失败！你指定的javdb网址有错误：' + path_relative + '\n')
                        continue  # 【退出对该jav的整理】
                # 用户没有指定网址，则去搜索
                else:
                    url_search_web = url_db + 'search?q=' + jav.car + '&f=all'
                    print('    >搜索车牌：', url_search_web)
                    # 得到javdb搜索网页html
                    html_web, cookies = get_search_db_html(url_search_web, cookies, proxy_db)
                    # 尝试找movie-box   0链接 1车牌
                    list_search_results = re.findall(r'href="/v/(.+?)" class="box" title=".+?"[\s\S]*?uid">(.+?)</div>', html_web, re.DOTALL)  # 匹配处理“标题”
                    # print(list_search_results)
                    if list_search_results:  # 搜索结果页面只有一个box
                        # print(list_search_results)
                        # print('    >正在核查搜索结果...')
                        jav_pref = jav.car.split('-')[0]  # 匹配车牌的前缀字母
                        jav_suf = jav.car.split('-')[-1].lstrip('0')  # 当前车牌的后缀数字 去除多余的0
                        list_fit_results = []
                        for i in list_search_results:
                            url_num = i[1].upper()
                            url_suf = re.search(r'(\d\d+)', url_num).group(1).lstrip('0')  # 匹配box上影片url，车牌的后缀数字，去除多余的0
                            # print('url后缀：', url_suf)
                            if jav_suf == url_suf:  # 数字相同
                                url_pref = re.search(r'([A-Z]+2?)', url_num).group(1).upper()  # 匹配处理url所带车牌前面的字母“n”
                                # print('url前缀：', url_suf)
                                if jav_pref == url_pref:  # 数字相同的基础下，字母也相同，即可能车牌相同
                                    list_fit_results.append(i)
                            else:
                                continue  # 【退出对该jav的整理】
                        # 搜索结果一个都匹配不上
                        if not list_fit_results:
                            num_fail += 1
                            record_fail('    >第' + str(
                                num_fail) + '个失败！javdb找不到该车牌的信息：' + jav.car + '，' + path_relative + '\n')
                            # print(html_web)
                            continue  # 【退出对该jav的整理】
                        # 默认用第一个搜索结果
                        url_on_web = url_db + 'v/' + list_fit_results[0][0]
                        if len(list_fit_results) > 1:
                            num_fail += 1
                            record_fail('    >第' + str(
                                num_fail) + '个警告！javdb搜索到同车牌的不同视频：' + jav.car + '，' + path_relative + '\n')
                    # 找不到box
                    else:
                        num_fail += 1
                        record_fail('    >第' + str(
                            num_fail) + '个失败！javdb找不到该车牌的信息：' + jav.car + '，' + path_relative + '\n')
                        continue  # 【跳出对该jav的整理】
                # 经过上面的三种情况，可能找到了jav在web上的网页链接url_on_web
                print('    >获取信息：', url_on_web)
                # 得到最终的jav所在网页
                html_web, cookies = get_db_html(url_on_web, cookies, proxy_db)
                html = html_web
                # print(html_web)

                # 有大部分信息的html_web
                html_web = re.search(r'h2 class([\s\S]*?)想看', html_web, re.DOTALL).group(1)
                # print(html_web)
                # 标题
                title = re.search(r'strong>(.+?)</', html_web).group(1).replace(' 中文字幕 ', '')
                # 去除xml文档和windows路径不允许的特殊字符 &<>  \/:*?"<>|
                title = replace_xml_win(title)
                print('    >影片标题：', title)
                # title的开头是车牌号，想要后面的纯标题
                car_titleg = re.search(r'(.+?) (.+)', title)
                # 车牌号
                dict_data['车牌'] = car = car_titleg.group(1)
                # 给用户重命名用的标题是“短标题”，nfo中是“完整标题”，但用户在ini中只用写“标题”
                title_only = car_titleg.group(2)
                dict_data['完整标题'] = title_only
                # 处理影片的标题过长
                if len(title_only) > settings.int_title_len:
                    dict_data['标题'] = title_only[:settings.int_title_len]
                else:
                    dict_data['标题'] = title_only
                # DVD封面cover
                coverg = re.search(r'img src="(.+?)"', html_web)  # 封面图片的正则对象
                if str(coverg) != 'None':
                    url_cover = coverg.group(1)
                else:
                    url_cover = ''
                # 发行日期
                premieredg = re.search(r'(\d\d\d\d-\d\d-\d\d)', html_web)
                if str(premieredg) != 'None':
                    dict_data['发行年月日'] = time_premiered = premieredg.group(1)
                    dict_data['发行年份'] = time_premiered[0:4]
                    dict_data['月'] = time_premiered[5:7]
                    dict_data['日'] = time_premiered[8:10]
                else:
                    dict_data['发行年月日'] = time_premiered = '1970-01-01'
                    dict_data['发行年份'] = '1970'
                    dict_data['月'] = '01'
                    dict_data['日'] = '01'
                # 片长 <td><span class="text">150</span> 分钟</td>
                runtimeg = re.search(r'value">(\d+) 分鍾<', html_web)
                if str(runtimeg) != 'None':
                    dict_data['片长'] = runtimeg.group(1)
                else:
                    dict_data['片长'] = '0'
                # 片商 制作商
                studiog = re.search(r'makers/.+?">(.+?)<', html_web)
                if str(studiog) != 'None':
                    dict_data['片商'] = studio = replace_xml_win(studiog.group(1))
                else:
                    dict_data['片商'] = 'FC2卖家'
                    studio = ''
                # 特点
                genres = re.findall(r'tags.+?">(.+?)</a>', html_web)
                if bool_subtitle:  # 有“中字“，加上特征”中文字幕”
                    genres.append('中文字幕')
                try:
                    genres = [dict_genre[i] for i in genres if dict_genre[i] != '删除']
                except KeyError as error:
                    num_fail += 1
                    record_fail('    >第' + str(num_fail) + '个失败！发现新的特征需要添加至【特征对照表】：' + str(error) + '\n')
                    continue
                # print(genres)
                #######################################################################
                dict_data['视频'] = dict_data['原文件名'] = jav.name_no_ext  # dict_data['视频']，先定义为原文件名，即将发生变化。
                dict_data['原文件夹名'] = jav.folder
                # 是CD1还是CDn？
                num_all_episodes = dict_car_pref[jav.car]  # 该车牌总共多少集
                if num_all_episodes > 1:
                    str_cd = '-cd' + str(jav.episode)
                else:
                    str_cd = ''

                # 1重命名视频【相同】
                try:
                    dict_data, jav, num_temp = rename_mp4(jav, num_fail, settings, dict_data, list_name_video,
                                                          path_relative, str_cd)
                    num_fail = num_temp
                except FileExistsError:
                    num_fail += 1
                    continue

                # 2 归类影片【相同】只针对视频文件和字幕文件。注意：第2操作和下面（第3操作+第7操作）互斥，只能执行第2操作或（第3操作+第7操作），归类影片是针对“文件”还是“文件夹”。
                try:
                    jav, num_temp = classify_files(jav, num_fail, settings, dict_data, list_classify_basis,
                                                   root_classify)
                    num_fail = num_temp
                except FileExistsError:
                    num_fail += 1
                    continue

                # 3重命名文件夹【相同】如果是针对“文件”归类，这一步会被跳过。 因为用户只需要归类视频文件，不需要管文件夹。
                try:
                    jav, num_temp = rename_folder(jav, num_fail, settings, dict_data, list_name_folder,
                                                  bool_separate_folder, num_all_episodes)
                    num_fail = num_temp
                except FileExistsError:
                    num_fail += 1
                    continue

                # 更新一下path_relative
                path_relative = sep + jav.path.replace(root_choose, '')  # 影片的相对于所选文件夹的路径，用于报错

                # 4写入nfo【独特】
                if settings.bool_nfo:
                    # 如果是为空地准备的nfo，不需要多cd
                    if settings.bool_cd_only:
                        path_nfo = jav.root + sep + jav.name_no_ext.replace(str_cd, '') + '.nfo'
                    else:
                        path_nfo = jav.root + sep + jav.name_no_ext + '.nfo'
                    # nfo中tilte的写法
                    title_in_nfo = ''
                    for i in list_name_nfo_title:
                        title_in_nfo += dict_data[i]
                    # 开始写入nfo，这nfo格式是参考的kodi的nfo
                    f = open(path_nfo, 'w', encoding="utf-8")
                    f.write("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\" ?>\n"
                            "<movie>\n"
                            "  <title>" + title_in_nfo + "</title>\n"
                            "  <originaltitle>" + title + "</originaltitle>\n"
                            "  <year>" + dict_data['发行年份'] + "</year>\n"
                            "  <mpaa>NC-17</mpaa>\n"                            
                            "  <customrating>NC-17</customrating>\n"
                            "  <countrycode>JP</countrycode>\n"
                            "  <premiered>" + time_premiered + "</premiered>\n"
                            "  <release>" + time_premiered + "</release>\n"
                            "  <runtime>" + dict_data['片长'] + "</runtime>\n"
                            "  <country>日本</country>\n"
                            "  <studio>" + studio + "</studio>\n"
                            "  <id>" + car + "</id>\n"
                            "  <num>" + car + "</num>\n")
                    # 需要将特征写入genre
                    if settings.bool_genre:
                        for i in genres:
                            f.write("  <genre>" + i + "</genre>\n")
                        if settings.bool_write_studio and studio:
                            f.write("  <genre>卖家:" + studio + "</genre>\n")
                        if list_extra_genres:
                            for i in list_extra_genres:
                                f.write("  <genre>" + dict_data[i] + "</genre>\n")
                    # 需要将特征写入tag
                    if settings.bool_tag:
                        for i in genres:
                            f.write("  <tag>" + i + "</tag>\n")
                        if settings.bool_write_studio and studio:
                            f.write("  <tag>卖家:" + studio + "</tag>\n")
                        if list_extra_genres:
                            for i in list_extra_genres:
                                f.write("  <tag>" + dict_data[i] + "</tag>\n")
                    # 写入演员
                    f.write("  <actor>\n    <name>FC2演员</name>\n    <type>Actor</type>\n  </actor>\n")
                    f.write("</movie>\n")
                    f.close()
                    print('    >nfo收集完成')

                # 5需要两张封面图片【独特】
                if settings.bool_jpg:
                    path_fanart = jav.root + sep
                    path_poster = jav.root + sep
                    for i in list_name_fanart:
                        path_fanart += dict_data[i]
                    for i in list_name_poster:
                        path_poster += dict_data[i]
                        # kodi只需要一份图片，图片路径唯一
                    if settings.bool_cd_only:
                        path_fanart = path_fanart.replace(str_cd, '')
                        path_poster = path_poster.replace(str_cd, '')
                    # emby需要多份，现在不是第一集，直接复制第一集的图片
                    elif jav.episode != 1:
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
                        # 下载封面
                        print('    >从javdb下载封面：', url_cover)
                        try:
                            download_pic(url_cover, path_fanart, proxy_db)
                            print('    >fanart.jpg下载成功')
                        except:
                            num_fail += 1
                            record_fail('    >第' + str(
                                num_fail) + '个失败！下载fanart.jpg失败：' + url_cover + '，' + path_relative + '\n')
                            continue  # 退出对该jav的整理
                    # 裁剪生成 poster
                    if check_picture(path_poster):
                        # print('    >已有poster.jpg')
                        pass
                    elif settings.bool_face:
                        crop_poster_baidu(path_fanart, path_poster, client)
                        # 需要加上条纹
                        if settings.bool_watermark_subtitle and bool_subtitle:
                            add_watermark_subtitle(path_poster)
                        if settings.bool_watermark_divulge and bool_divulge:
                            add_watermark_divulge(path_poster)
                    else:
                        crop_poster_default(path_fanart, path_poster, 2)
                        # 需要加上条纹
                        if settings.bool_watermark_subtitle and bool_subtitle:
                            add_watermark_subtitle(path_poster)
                        if settings.bool_watermark_divulge and bool_divulge:
                            add_watermark_divulge(path_poster)

                # 6收集演员头像【相同】

                # 7归类影片，针对文件夹【相同】
                try:
                    num_temp = classify_folder(jav, num_fail, settings, dict_data, list_classify_basis, root_classify,
                                               root, bool_separate_folder, num_all_episodes)
                    num_fail = num_temp
                except FileExistsError:
                    num_fail += 1
                    continue

            except:
                num_fail += 1
                record_fail('    >第' + str(num_fail) + '个失败！发生错误，如一直在该影片报错请截图并联系作者：' + path_relative + '\n' + format_exc() + '\n')
                continue     # 【退出对该jav的整理】

    # 完结撒花
    print('\n当前文件夹完成，', end='')
    if num_fail > 0:
        print('失败', num_fail, '个!  ', root_choose, '\n')
        line = -1
        with open('【可删除】失败记录.txt', 'r', encoding="utf-8") as f:
            content = list(f)
        while 1:
            if content[line].startswith('已'):
                break
            line -= 1
        for i in range(line+1, 0):
            print(content[i], end='')
        print('\n“【可删除】失败记录.txt”已记录错误\n')
    else:
        print(' “0”失败！  ', root_choose, '\n')
    # os.system('pause')
    input_start_key = input('回车继续选择文件夹整理：')
