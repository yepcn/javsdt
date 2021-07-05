# -*- coding:utf-8 -*-
import re, os, requests
from Class.EnumStatus import StatusScrape
from Functions.Requests.JavlibraryReq import get_library_html
# from traceback import format_exc

# 搜索javbus，或请求javbus上jav所在网页，返回html
def get_bus_html(url, proxy):
    for retry in range(10):
        try:
            if proxy:       # existmag=all为了 获得所有影片，而不是默认的有磁力的链接
                rqs = requests.get(url, proxies=proxy, timeout=(6, 7), headers={'Cookie': 'existmag=all'})
            else:
                rqs = requests.get(url, timeout=(6, 7), headers={'Cookie': 'existmag=all'})
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
        if re.search(r'JavBus', rqs_content):
            return rqs_content
        else:
            print('    >打开网页失败，空返回...重新尝试...')
            continue
    print('>>请检查你的网络环境是否可以打开：', url)
    os.system('pause')


# 去javbus搜寻系列、在javbus的封面链接
# 返回：系列名称，图片链接，状态码
def find_series_cover_genres_bus(jav_model, url_bus, proxy):
    # jav在javbus上的url，一般就是javbus网址/车牌
    url_jav_bus = f'{url_bus}/{jav_model.Car}'
    print('    >获取补充信息：', url_jav_bus)
    # 获得影片在javbus上的网页
    html_jav_bus = get_bus_html(url_jav_bus, proxy)
    if not re.search(r'404 Page', html_jav_bus):
        pass
    # 这部jav在javbus的网址不简单
    else:
        # 还是老老实实去搜索
        url_search_bus = f'{url_bus}/search/{jav_model.Car.replace("-", "")}&type=1&parent=ce'
        print('    >搜索javbus：', url_search_bus)
        html_search_bus = get_bus_html(url_search_bus, proxy)
        # 搜索结果的网页，大部分情况一个结果，也有可能是多个结果的网页
        # 尝试找movie-box
        list_search_results = re.findall(r'movie-box" href="(.+?)">', html_search_bus)  # 匹配处理“标题”
        if list_search_results:
            pref = jav_model.Car.split('-')[0]  # 匹配车牌的前缀字母
            suf = jav_model.Car.split('-')[-1].lstrip('0')  # 当前车牌的后缀数字 去除多余的0
            list_fit_results = []  # 存放，车牌符合的结果
            for i in list_search_results:
                url_end = i.split('/')[-1].upper()
                url_suf = re.search(r'[-_](\d+)', url_end).group(1).lstrip('0')  # 匹配box上影片url，车牌的后缀数字，去除多余的0
                if suf == url_suf:  # 数字相同
                    url_pref = re.search(r'([A-Z]+2?8?)', url_end).group(1).upper()  # 匹配处理url所带车牌前面的字母“n”
                    if pref == url_pref:  # 数字相同的基础下，字母也相同，即可能车牌相同
                        list_fit_results.append(i)
            # 有结果
            if list_fit_results:
                # 有多个结果，发个状态码，警告一下用户
                if len(list_fit_results) > 1:
                    status = StatusScrape.bus_multiple_search_results
                # 默认用第一个搜索结果
                url_first_result = list_fit_results[0]
                print('    >获取系列：', url_first_result)
                html_jav_bus = get_bus_html(url_first_result, proxy)
            else:
                status = StatusScrape.bus_not_found
                html_jav_bus = ''
        else:
            status = StatusScrape.bus_not_found
            html_jav_bus = ''

    genres = []
    if html_jav_bus:
        # DVD封面cover
        coverg = re.search(r'bigImage" href="/pics/cover/(.+?)"', html_jav_bus)
        if str(coverg) != 'None':
            jav_model.Javbus = f'{url_bus}{coverg.group(1)}'
        # 系列:</span> <a href="https://www.cdnbus.work/series/kpl">悪質シロウトナンパ</a>
        seriesg = re.search(r'系列:</span> <a href=".+?">(.+?)</a>', html_jav_bus)
        if seriesg and not jav_model.Series:
            jav_model.Series = seriesg.group(1)
        # 特点
        genres = re.findall(r'gr_sel" value="\d+"><a href=".+">(.+?)</a>', html_jav_bus)
    return status, genres

