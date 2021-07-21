import os
# file = 'http://pics.dmm.co.jp/mono/movie/adult/172real380/172real380pl.jpg'
# print(os.path.basename(file))
# type1 = os.path.splitext(file)
# print(type1)
# print(type1[0])

# def change_dict(dict):
#     dict['A'] = 'B'
#
# dict = {'A': 'S', }
# change_dict(dict)
# print(dict)


# def change_int(int_a):
#     int_a = 3
#
# int_b = 1
# change_int(int_b)
# print(int_b)

#
#
# try:
#     test()
# except FileExistsError as e:
#     print(f"已存在{e}" )


class MyError(Exception):
   pass

def test():
    raise MyError("我的电脑")



try:
    test()
except MyError as e:
    print(f"已存在{e}" )