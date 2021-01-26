# -*- coding:utf-8 -*-
import re, os, requests, time
# from traceback import format_exc

# 功能：请求各大jav网站和arzon的网页
# 参数：网址url，请求头部header/cookies，代理proxy
# 返回：网页html，请求头部


#################################################### javdb ########################################################
# 搜索javdb，得到搜索结果网页，返回html。
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
    print('>>请检查你的网络环境是否可以打开：', url)
    os.system('pause')


# 请求jav在javdb上的网页，返回html
def get_db_html(url, cookies, proxy):
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
    print('>>请检查你的网络环境是否可以打开：', url)
    os.system('pause')

