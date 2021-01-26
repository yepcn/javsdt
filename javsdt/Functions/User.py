# -*- coding:utf-8 -*-
import sys
from os import sep, system
from os.path import exists, isdir
from time import sleep
from tkinter import filedialog, Tk, TclError


# 功能：获取用户选取的文件夹路径
# 参数：无
# 返回：路径str
# 辅助：tkinter.Tk，tkinter.filedialog，os.sep，sys
def choose_directory():
    # 用户：选择需要整理的文件夹
    print('请选择要整理的文件夹：', end='')
    for i in range(2):
        try:
            directory_root = Tk()
            directory_root.withdraw()
            path_work = filedialog.askdirectory()
            if path_work == '':
                print('你没有选择目录! 请重新选：')
                sleep(2)
                continue
            else:
                # askdirectory 获得是 正斜杠 路径C:/，所以下面要把 / 换成 反斜杠\
                return path_work.replace('/', sep)
        except TclError:  # 来自@BlueSkyBot
            try:
                path_work = input("请输入你需要整理的文件夹路径: ")
            except KeyboardInterrupt:
                sys.exit('输入终止，马上退出！')
            if not exists(path_work) or not isdir(path_work):
                print('\"{0}\" 不存在当前目录或者输入错误，请重新输入！'.format(path_work))
                sleep(2)
                continue
            else:
                return path_work
    print('你可能不需要我了，请关闭我吧！')
    system('pause')