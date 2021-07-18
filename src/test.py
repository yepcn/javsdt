import os
# file = 'http://pics.dmm.co.jp/mono/movie/adult/172real380/172real380pl.jpg'
# print(os.path.basename(file))
# type1 = os.path.splitext(file)
# print(type1)
# print(type1[0])

def change_dict(dict):
    dict['A'] = 'B'

dict = {'A': 'S', }
change_dict(dict)
print(dict)
