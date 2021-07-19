# -*- coding:utf-8 -*-
import re, os, requests, time
# from traceback import format_exc


# 搜索javdb，得到搜索结果网页，返回html。
from MyEnum import ScrapeStatusEnum
from JavModel import JavModel


def get_search_db_html(url, cookies, proxy):
    for retry in range(1, 11):
        if retry % 4 == 0:
            print('    >睡眠5分钟...')
            time.sleep(300)
        try:
            if proxy:
                rqs = requests.get(url, cookies=cookies, proxies=proxy, timeout=(6, 7))
            else:
                rqs = requests.get(url, cookies=cookies, timeout=(6, 7))
        except requests.exceptions.ProxyError:
            # print(format_exc())
            print('    >通过局部代理失败，重新尝试...')
            continue
        except:
            # print(format_exc())
            print('    >打开网页失败，重新尝试...')
            continue
        rqs.encoding = 'utf-8'
        rqs_content = rqs.text
        if re.search(r'JavDB', rqs_content):
            if re.search(r'搜索結果', rqs_content):
                return rqs_content, cookies
            elif re.search(r'登入 | JavDB', rqs_content):
                cfduid = input('请输入cfduid：')
                jdb_session = input('请输入jdb_session：')
                cookies = {
                    "__cfduid": cfduid,
                    "_jdb_session": jdb_session,
                }
            else:
                print('    >睡眠5分钟...')
                time.sleep(300)
                continue
        else:
            print('    >打开网页失败，空返回...重新尝试...')
            continue
    input(f'>>请检查你的网络环境是否可以打开：{url}')


# 请求jav在javdb上的网页，返回html
def get_db_html_by_cookies(url, cookies, proxy):
    for retry in range(1, 11):
        if retry % 4 == 0:
            print('    >睡眠5分钟...')
            time.sleep(300)
        try:
            if proxy:
                rqs = requests.get(url, cookies=cookies, proxies=proxy, timeout=(6, 7))
            else:
                rqs = requests.get(url, cookies=cookies, timeout=(6, 7))
        except requests.exceptions.ProxyError:
            # print(format_exc())
            print('    >通过局部代理失败，重新尝试...')
            continue
        except:
            # print(format_exc())
            print('    >打开网页失败，重新尝试...')
            continue
        rqs.encoding = 'utf-8'
        rqs_content = rqs.text
        # print(rqs_content)
        if re.search(r'JavDB', rqs_content):
            if re.search(r'link rel="canonical"', rqs_content):
                return rqs_content, cookies
            elif re.search(r'登入 | JavDB', rqs_content):
                cfduid = input('请粘贴cfduid：')
                jdb_session = input('请粘贴jdb_session：')
                cookies = {
                    "__cfduid": cfduid,
                    "_jdb_session": jdb_session,
                }
            else:
                print('    >睡眠5分钟...')
                time.sleep(300)
                continue
        else:
            print('    >打开网页失败，空返回...重新尝试...')
            continue
    input(f'>>请检查你的网络环境是否可以打开：{url}')


# 请求jav在javdb上的网页，返回html
def get_db_html(url, proxy):
    for retry in range(1, 11):
        try:
            if proxy:
                rqs = requests.get(url, proxies=proxy, timeout=(6, 7))
            else:
                rqs = requests.get(url, timeout=(6, 7))
        except requests.exceptions.ProxyError:
            # print(format_exc())
            print('    >通过局部代理失败，重新尝试...')
            continue
        except:
            # print(format_exc())
            print('    >打开网页失败，重新尝试...')
            continue
        rqs.encoding = 'utf-8'
        rqs_content = rqs.text
        # print(rqs_content)
        if re.search(r'link rel="canonical"', rqs_content):
            return rqs_content
        else:
            print('    >打开网页失败，空返回...重新尝试...')
            continue
    input(f'>>请检查你的网络环境是否可以打开：{url}')


def scrape_from_db(jav_file, jav_model, url_db, proxy_db):
    # 用户指定了网址，则直接得到jav所在网址
    if '仓库' in jav_file.name:
        url_appointg = re.search(r'仓库(\w+?)', jav_file.name)
        if url_appointg:
            jdvdb = url_appointg
            html_jav_db = get_db_html(f'{url_db}/v/{jdvdb}', proxy_db)
            if re.search(r'頁面未找到', html_jav_db):
                return ScrapeStatusEnum.db_specified_url_wrong, []
        else:
            # 指定的javlibrary网址有错误
            return ScrapeStatusEnum.db_specified_url_wrong, []

    # 用户没有指定网址，则去搜索
    else:   # https://javdb9.com/video_codes/PKPD
        car_pref, car_suf = jav_file.car.split("-")
        car_suf = int(re.search(r'(\d+)\w*', car_suf).group(1))
        url_car_pref = f'{url_db}/video_codes/{car_pref}'
        html_pref_1 = get_db_html(url_car_pref, proxy_db)
        # uid">PKPD-154</div>
        list_boxs = re.findall(r'href="/v/(.+?)" class="box" title=".+?"[\s\S]*?uid">\w+-(\d+)[a-z]*</div>',
                               html_pref_1, re.DOTALL)
        # 没有该车牌的codes页面
        if not list_boxs:
            return ScrapeStatusEnum.db_not_found, []
        else:
            car_suf_min = int(list_boxs[-1][1])
            # 就在当前页
            if car_suf > car_suf_min:
                javdb = find_javdb_code(car_suf, list_boxs)
                if not javdb:
                    return ScrapeStatusEnum.db_not_found, []
            elif car_suf == car_suf_min:
                javdb = list_boxs[-1][0]
            else:    # ?page=3
                no_page = (car_suf - car_suf_min) % 40 + 2
                url_target_page_n = f'{url_db}/video_codes?page={no_page}'
                html_pref_n = get_db_html(url_target_page_n, proxy_db)
                list_boxs_n = re.findall(r'href="/v/(.+?)" class="box" title=".+?"[\s\S]*?uid">\w+-(\d+)[a-z]*</div>',
                                         html_pref_n, re.DOTALL)
                suf_current_min = list_boxs_n[-1][1]
                suf_current_max = list_boxs_n[0][1]
                if suf_current_max >= car_suf >= suf_current_min:
                    javdb = find_javdb_code(car_suf, list_boxs_n)
                    if not javdb:
                        return ScrapeStatusEnum.db_not_found, []
                elif car_suf > suf_current_max:
                    url_target_page_m = f'{url_db}/v/{no_page - 1}'
                    html_pref_m = get_db_html(url_target_page_m, proxy_db)
                    list_boxs_m = re.findall(r'href="/v/(.+?)" class="box" title=".+?"[\s\S]*?uid">\w+-(\d+)[a-z]*</div>',
                                             html_pref_m, re.DOTALL)
                    javdb = find_javdb_code(car_suf, list_boxs_m)
                    if not javdb:
                        return ScrapeStatusEnum.db_not_found, []
                else:
                    # car_suf < car_suf_current_min:
                    url_target_page_o = f'{url_db}/v/{no_page + 1}'
                    html_pref_o = get_db_html(url_target_page_o, proxy_db)
                    list_boxs_o = re.findall(r'href="/v/(.+?)" class="box" title=".+?"[\s\S]*?uid">\w+-(\d+)[a-z]*</div>',
                                             html_pref_o, re.DOTALL)
                    javdb = find_javdb_code(car_suf, list_boxs_o)
                    if not javdb:
                        return ScrapeStatusEnum.db_not_found, []
    # 得到 javdb
    # return StatusScrape.success, javdb
    url_jav_db = f'{url_db}/v/{javdb}'
    print('    >获取信息：', url_jav_db)
    html_jav_db = get_db_html(url_jav_db, proxy_db)
    # <title> BKD-171 母子交尾 ～西会津路～ 中森いつき | JavDB 成人影片資料庫及磁鏈分享 </title>
    car_title = re.search(r'title> (.+?) | JavDB', html_jav_db).group(1)
    list_car_title = car_title.split(' ', 1)
    jav_model.Car = list_car_title[0]  # 围绕该jav的所有信息
    jav_model.Title = list_car_title[1]
    jav_model.Javdb = javdb
    # 带着主要信息的那一块 複製番號" data-clipboard-text="BKD-171">
    html_jav_db = re.search(r'複製番號([\s\S]+?)存入清單', html_jav_db, re.DOTALL).group(1)
    # 系列 "/series/RJmR">○○に欲望剥き出しでハメまくった中出し記録。</a>
    seriesg = re.search(r'series/.+?">(.+?)</a>', html_jav_db)
    jav_model.Series = seriesg.group(1) if seriesg else ''
    # 上映日 e">2019-02-01<
    releaseg = re.search(r'(\d\d\d\d-\d\d-\d\d)', html_jav_db)
    jav_model.Release = releaseg.group(1) if releaseg else '1970-01-01'
    # 片长 value">175 分鍾<
    runtimeg = re.search(r'value">(\d+) 分鍾<', html_jav_db)
    jav_model.Runtime = int(runtimeg.group(1)) if runtimeg else 0
    # 导演 /directors/WZg">NABE<
    directorg = re.search(r'directors/.+?">(.+?)<', html_jav_db)
    jav_model.Director = directorg.group(1) if directorg else ''
    # 制作商 e"><a href="/makers/
    studiog = re.search(r'makers/.+?">(.+?)<', html_jav_db)
    jav_model.Studio = studiog.group(1) if studiog else ''
    # 发行商 /publishers/pkAb">AV OPEN 2018</a><
    publisherg = re.search(r'publishers.+?">(.+?)</a><', html_jav_db)
    jav_model.Publisher = publisherg.group(1) if publisherg else ''
    # star gray"></i></span>&nbsp;3.75分
    scoreg = re.search(r'star gray"></i></span>&nbsp;(.+?)分', html_jav_db)
    jav_model.Score = int(float(scoreg.group(1)) * 20) if scoreg else 0
    # 演员们 /actors/M0xA">上川星空</a>  actors/P9mN">希美まゆ</a><strong class="symbol female
    actors = re.findall(r'actors/.+?">(.+?)</a><strong class="symbol female', html_jav_db)
    jav_model.Actors = [i.strip() for i in actors]
    print('    >演员：', actors)
    # 特征 /tags?c7=8">精选、综合</a>
    genres_db = re.findall(r'tags.+?">(.+?)</a>', html_jav_db)
    return ScrapeStatusEnum.success, genres_db


def find_javdb_code(car_suf, list_boxs):
    javdb = ''
    for box in list_boxs:
        if box[1] == car_suf:
            javdb = box[0]
    return javdb
