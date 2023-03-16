import os
import sqlite3
import json
import numpy as np

class JsonEncoder(json.JSONEncoder):
    # 用于处理写json文件格式问题
    def default(self, obj):
        if isinstance(obj, (np.integer, np.floating, np.bool_)):
            return obj.item()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(JsonEncoder, self).default(obj)

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def select(dbpath,sql_str):
    con = sqlite3.connect(dbpath) #打开数据库
    con.row_factory = dict_factory
    c = con.cursor()
    c.execute(sql_str)
    output = c.fetchall()
    return output

def return_img_stream(img_local_path):
    """
    工具函数:
    获取本地图片流
    :param img_local_path:文件单张图片的本地绝对路径
    :return: 图片流
    """
    import base64
    img_stream = ''
    with open(img_local_path, 'rb') as img_f:
        img_stream = img_f.read()
        img_stream = base64.b64encode(img_stream).decode()
    return img_stream

def imgexists(fullpath):
    # 图片找不到时用空白图替代
    if os.path.exists(fullpath+".png"):
        return {"note":"png","streamimg":return_img_stream(fullpath+".png")}
    elif os.path.exists(fullpath+".jpg"):
        return {"note":"jpg","streamimg":return_img_stream(fullpath+".jpg")}
    
    # return "这里是图片"
    return {"note":"暂缺.png","streamimg":return_img_stream("data/暂缺.png")}

if __name__ == '__main__':
    print("yes")