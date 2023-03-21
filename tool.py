import os
import sqlite3
import json
import numpy as np
import pandas as pd
import opencc
cc = opencc.OpenCC("s2t")
# ddb数据
with open("data/ddbc/ddbc_name2aid.json","r",encoding="utf8") as f:
    ddbc_name2aid = json.load(f)
with open("data/ddbc/ddbc_person_info.json","r",encoding="utf8") as f:
    ddbc_personinfo = json.load(f)
ddbc_place=pd.read_excel("data/ddbc/place_all.xlsx")
dbpath1="data/latest.db"


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
    con = sqlite3.connect(dbpath1) #打开数据库
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


def sort_name2id(name2id):
    # 把name2id重新排序一下
    from functools import cmp_to_key
    idlist=name2id.values()
    print(idlist)
    sql="select c_dy,c_personid from BIOG_main where c_personid in {}".format(tuple(idlist) if len(idlist) > 1 else "({})".format(idlist[0]))
    outs=select("",sql)
    id2dy={}
    for out in outs:
        id2dy[out["c_personid"]]=out["c_dy"]
    print(id2dy)
    def cmp(s1, s2):
        
        if s1[1]=="unknow":ss1=99999999
        else:ss1=id2dy[s1[1]]
        if s2[1]=="unknow":ss2=99999999
        else:ss2=id2dy[s2[1]]
        if ss2 > ss1:return -1
        elif ss2 == ss1:return 0
        else:return 1
    name2id = sorted(name2id.items(),key=cmp_to_key(cmp))
    # newname2id={}
    # for t in name2id:
    #     newname2id[t[0]]=t[1]

    return name2id


if __name__ == '__main__':
   name2id= { "(愛新覺羅)溥儀": 439438, 
      "佚名": "unknow", 
      "傅山": 30248, 
      "吳景運": 352236, 
      "周密": 10183, 
      "张三": "unknow", 
      "張南陽": "unknow", 
      "張應甲": "unknow", 
      "張翀": 70447, 
      "張若麒": 58452, 
      "愛新覺羅弘曆": 55870, 
      "愛新覺羅顒琰": 63427, 
      "文彭": 34677, 
      "曹溶": 34911, 
      "梁清標": 58585, 
      "楊載": 28399, 
      "歐陽玄": 10815, 
      "石濤": 438086, 
      "範杼": "unknow", 
      "納蘭性德": 65803, 
      "董其昌": 35003, 
      "詹景鳳": 438804, 
      "趙孟頫": 17690, 
      "錢溥": 133126, 
      "項元汴": 30328}
   print(sort_name2id(name2id))