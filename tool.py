import os
import sqlite3
import json
import numpy as np
import opencc
cc = opencc.OpenCC("s2t")
with open("data/ddbc/ddbc_name2aid.json","r",encoding="utf8") as f:
    ddbc_name2aid = json.load(f)
with open("data/ddbc/ddbc_person_info.json","r",encoding="utf8") as f:
    ddbc_personinfo = json.load(f)
dbpath="data/latest.db"


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

def makecname2id(addnames,addcids):
    # 新增人物列表预处理
    cname2id = {}
    for addname,addcid in zip(addnames,addcids):
        if addcid=="unknow":
            cname2id[addname]="unknow"
        elif addcid=="":break    
        else:
            cname2id[addname]=int(addcid)
    return cname2id

def delauname(oldname):
    # 预处理作者人名
    
    # 需要将人名转为繁体，去掉()和·
    newname= cc.convert(oldname).split("（")[0].replace("·","")
    if newname=="清高宗":newname="愛新覺羅弘曆"
    if newname=="愛新覺羅溥儀":newname="(愛新覺羅)溥儀"
    return newname

if __name__ == '__main__':
    print("yes")