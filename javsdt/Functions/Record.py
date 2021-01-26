# -*- coding:utf-8 -*-
from time import strftime, localtime, time


# 功能：记录整理的文件夹、整理的时间
# 参数：错误信息
# 返回：无
# 辅助：os.strftime, os.localtime, os.time,
def record_start(root_choose):
    msg = '已选择文件夹：' + root_choose + '  ' + strftime('%Y-%m-%d %H:%M:%S', localtime(time())) + '\n'
    txt = open('【可删除】失败记录.txt', 'a', encoding="utf-8")
    txt.write(msg)
    txt.close()
    txt = open('【可删除】警告信息.txt', 'a', encoding="utf-8")
    txt.write(msg)
    txt.close()
    txt = open('【可删除】新旧文件名清单.txt', 'a', encoding="utf-8")
    txt.write(msg)
    txt.close()


# 功能：记录错误信息
# 参数：错误信息
# 返回：无
# 辅助：无
def record_fail(fail_msg):
    print(fail_msg, end='')
    txt = open('【可删除】失败记录.txt', 'a', encoding="utf-8")
    txt.write(fail_msg)
    txt.close()


# 功能：记录警告信息
# 参数：警告信息
# 返回：无
# 辅助：无
def record_warn(warn_msg):
    txt = open('【可删除】警告信息.txt', 'a', encoding="utf-8")
    txt.write(warn_msg)
    txt.close()


# 功能：记录旧文件名
# 参数：新文件名，旧文件名
# 返回：无
# 辅助：无
def record_video_old(name_new, name_old):
    txt = open('【可删除】新旧文件名清单.txt', 'a', encoding="utf-8")
    txt.write('<<<< ' + name_old + '\n')
    txt.write('>>>> ' + name_new + '\n')
    txt.close()