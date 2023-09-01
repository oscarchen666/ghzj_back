import os
import re
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
    return {"note":fullpath+"暂缺","streamimg":return_img_stream("data/暂缺.png")}

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
    if newname=="孫克弘":newname="孫克宏"
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

def dealyearstring(string):
    #处理时间字符串，输出对应的年份和朝代
    print(string)
    xyzzpp="(?<=元)[前零一二三四五六七八九十]+(?=年)"#西元和年之间的年份字符
    qtzzpp="[元一二三四五六七八九十]+(?=年)"#年之前的年份字符
    tgdzzzpp="[甲乙丙丁戊己庚辛壬癸]+[子丑寅卯辰巳午未申酉戌亥]+"
    zw2int={'一': "1", '二': "2", '三': "3", '四': "4", '五': "5", '六': "6",'七': "7", 
            '八': "8", '九': "9", '零': "0",'十':'','前':'-','元':"1"} # 年份转成数字
    # 定义天干地支列表
    tian_gan = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    di_zhi = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    # 定义天干地支转换函数
    def convert_tiangandizhi2num(string):
        tian_gan_num = tian_gan.index(string[0]) + 1
        di_zhi_num = di_zhi.index(string[1]) + 1
        return (tian_gan_num - 1) * 12 + di_zhi_num
    # res=[{"year":"unknow"}]
    if "西元" in string or "公元" in string:
        numstring = re.findall(xyzzpp, string)
        # print(numstring)
        if numstring:
            yearnum=""
            for n in numstring[0]:
                yearnum+=zw2int[n]
            res=[{  
                    "dynasty":"unknow",
                    "year":int(yearnum),
                    "nianhao":"根据公元年份直接获得"
                }]
            sql = "select c_dynasty_chn from dynasties where \
                    c_start <= {} and c_end >= {}".format(yearnum,yearnum)
            outs = select("",sql)
            if outs:
                res=[{  
                        "dynasty":out["c_dynasty_chn"],
                        "year":int(yearnum),
                        "nianhao":"根据公元年份直接获得"
                    }for out in outs]
            return res
    numstring = re.findall(qtzzpp, string)# 匹配年号+数字+年
    # print(numstring)
    if numstring:
        yearnum=""
        for n in numstring[0]:#该年号下的第几年
            yearnum+=zw2int[n]
        if yearnum=='':yearnum="10"#处理十年问题
        #计算年号起始年
        nianhao=cc.convert(string.split(numstring[0]+"年")[0])#数字前面的词
        # print(nianhao)
        sql="select c_dynasty_chn,c_nianhao_chn,c_firstyear,c_lastyear\
            from nian_hao where c_nianhao_chn ='{}'".format(nianhao)
        # sql = "select c_dynasty_chn,c_nianhao_chn,c_firstyear from nian_hao"
        outs =select("",sql)
        if outs:
            res=[]
            for out in outs:
                # if out["c_firstyear"]
                overflag=""
                if out["c_firstyear"]:
                    finyear=int(yearnum)+out["c_firstyear"]-1 # 起始年+该年号下的第几年-1
                    if out["c_firstyear"]<0 and finyear>=0: finyear+=1 # 没有公元0年，需要加一
                    if finyear > out["c_lastyear"]: overflag="(超过该年号结束年)"
                else:finyear="unknow"
                res.append({
                    "dynasty":out["c_dynasty_chn"],
                    "nianhao":nianhao+overflag,
                    "year":finyear
                })
            return res
    numstring = re.findall(tgdzzzpp, string)# 匹配年号+数字+年
    # print(numstring)
    if numstring:
        yearnum= convert_tiangandizhi2num(numstring[0])
        # print(yearnum)
        nianhao=cc.convert(string.split(numstring[0])[0])#数字前面的词     
        sql="select c_dynasty_chn,c_nianhao_chn,c_firstyear,c_lastyear\
            from nian_hao where c_nianhao_chn ='{}'".format(nianhao)
        # sql = "select c_dynasty_chn,c_nianhao_chn,c_firstyear from nian_hao"
        outs =select("",sql)
        if outs:
            res=[]
            for out in outs:
                finyear="unknow"
                overflag= ""
                if out["c_firstyear"] and out["c_lastyear"]:
                    overflag= "期间没有{}年".format(numstring[0])
                    # 查询哪一年天干地支符合要求
                    for year in range(out["c_firstyear"],out["c_lastyear"]+1):
                        yeartgdz=((year-3)%10-1)*12+((year-3)%12)
                        # print(year,yeartgdz)
                        if yeartgdz==yearnum:
                            finyear=year
                            overflag=""                           
                res.append({
                    "dynasty":out["c_dynasty_chn"],
                    "nianhao":nianhao+overflag,
                    "year":finyear
                })
            return res    

                
    return [{"year":"unknow"}]

if __name__ == '__main__':
    string="乾隆戊辰（西元一七四八年）春日"
    # string="崇祯元年"
    # string="乾隆戊辰"
    # string="建平三年"
    print(dealyearstring(string))