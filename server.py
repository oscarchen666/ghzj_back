import json
import os
import math
import pandas as pd
import opencc

from ner.getresulthc import infer,JsonEncoder
from ner.dealsent import getsentences,predealh
from ner.findperson import searchfen,select
from imgtool import return_img_stream,imgexists
from assoc.cbdb_dao import CBDBDAO

def ner_search(pid):
    # ner生成并搜索    
    # 写ner生成部分的代码时考虑批量处理，所以放在一个列表里
    filefroms = [pid+".json"]
    ss,author = getsentences("orig/"+pid+".json")
    forisents=[ss]
    dealsents=[predealh(ss)]
    authors=[author]
    # 生成ner结果
    results = infer(forisents,dealsents,filefroms,authors)
    # 在数据库中查询人物
    new_data = searchfen(results[0])
    # 存储并转码
    with open("nerresult/"+pid+".json","w",encoding="UTF8")as f:
        json.dump(new_data, f,indent=2, ensure_ascii=False,cls=JsonEncoder)
    with open("nerresult/"+pid+".json","r",encoding="UTF8")as f:
        data = json.load(f)
    return data

def ciyun(pid):
    # 通过ner结果得到词云数据和印章作者
    with open("nerresult/"+pid+".json","r",encoding="UTF8")as f:
        data = json.load(f)
    plist={}
    llist={}
    tlist={}
    wlist={}
    authorlist=[]
    for sentence in data["sentences"]:
        if sentence["author"] =="清高宗":sentence["author"]="愛新覺羅弘曆"
        authorlist.append(sentence["author"])
        for span in sentence["output"]:
            if span["type"]=="PersonName": #人名直接使用题跋里的名字，无论原名别名
                if span["span"]in plist:
                    plist[span["span"]]=plist[span["span"]]+1
                else:
                    plist[span["span"]]=1
            elif span["type"]=="Location":
                if span["span"]in llist:
                    llist[span["span"]]=llist[span["span"]]+1
                else:
                    llist[span["span"]]=1
            elif span["type"]=="Time":
                if span["span"]in tlist:
                    tlist[span["span"]]=tlist[span["span"]]+1
                else:
                    tlist[span["span"]]=1
            elif span["type"]=="Thing":
                if span["span"]in wlist:
                    wlist[span["span"]]=wlist[span["span"]]+1
                else:
                    wlist[span["span"]]=1

    cyres = {
        "PersonName":plist,
        "Location":llist,
        "Time":tlist,
        "Thing":wlist
    }
    return cyres

def authorlist(pid):
    # 印章作者列表
    save_path = "authorinfo/"+pid+".json"
    if os.path.exists(save_path):
        with open(save_path,"r",encoding="UTF8")as f:
            result = json.load(f)
        return result
    cc = opencc.OpenCC("s2t")
    yzdf = pd.read_csv("authorinfo/yzres.csv",encoding="UTF8")
    audf = pd.read_excel("authorinfo/人物的鉴藏画作个数.xlsx")
    alist = list(yzdf[yzdf["pid"]==int(pid)]["top1_作者"].values)
    result = {}
    aulist = list(set(alist))
    for au in aulist:
        result[cc.convert(au).split("（")[0].replace("·","")]={   
            # 需要将人名转为繁体，去掉()和·
            "本幅":int(alist.count(au)),
            "总数":int(audf[audf["top1_作者"]==au]["鉴藏画作数量"].values[0])
            }
    # 题跋作者
    with open("nerresult/"+pid+".json","r",encoding="UTF8")as f:
        data = json.load(f)
    for sentence in data["sentences"]:
        if sentence["author"] =="清高宗":sentence["author"]="愛新覺羅弘曆"
        if sentence["author"] in result:
            result[sentence["author"]]["本幅"]=result[sentence["author"]]["本幅"]+1
            result[sentence["author"]]["总数"]=result[sentence["author"]]["本幅"]+1
        else:
            result[sentence["author"]]={"本幅":1,"总数":1}

    # 查询朝代和cid
    for au in result:
        sql = "select c_personid,c_dy from BIOG_MAIN where c_name_chn = '"+au+"' or c_personid in (select c_personid from ALTNAME_DATA where c_alt_name_chn=  '"+au+"')" 
        out = select("latest.db",sql)
        if out:
            result[au]["朝代"]=out[0]["c_dy"]
            result[au]["cid"]=out[0]["c_personid"]

    with open(save_path,"w",encoding="UTF8") as f:
        json.dump(result, f,indent=2, ensure_ascii=False)
    return result

def lianxian(pid,name):
    # 作者和词云、图像连线
    # 和词云连线
    cylines = []
    with open("nerresult/"+pid+".json","r",encoding="UTF8")as f:
        tbdata = json.load(f)
    for sentence in tbdata["sentences"]:
        if sentence["author"]!=name:continue # 只统计指定作者的提拔
        for span in sentence["output"] :
            if span["type"]=="Person":continue # 非人名的人实体不统计
            info = {
                "type":span["type"],
                "text":span["span"]
            }
            # if span["type"]=="PersonName":
            #     info["text"]=span["name"]
            cylines.append(info)

    lines={
        "cylines":cylines,
        "hzlines":[]
    }
    return lines

def gaoliang(pid,name,type):
    # 选中词云、题跋原文中的实体时高亮其他相同实体
    with open("nerresult/"+pid+".json","r",encoding="UTF8")as f:
        tbdata = json.load(f)
    gllist=[]
    for i in range(len(tbdata["sentences"])):
        for span in tbdata["sentences"][i]["output"]:
            if type=="PersonName":#点击词云中的人名，根据人名去查找
                if span["type"]=="PersonName" and span["span"]==name:
                    gllist.append({"senid":i,"start":span["start"],"end":span["end"]})
            else:
                if span["type"]==type and span["span"]==name:
                    gllist.append({"senid":i,"start":span["start"],"end":span["end"]})
    result = {"name":name,"gllist":gllist}
    return result


def assocdata(name):
    # 国画大数据的关系图谱
    data_csv = pd.read_csv(r'data.csv')
    row = data_csv[data_csv['authorNameTC'] == name]

    if len(row) == 0 or math.isnan(row['cid']) == True:
        return  {
            'id':'',
            'id2name': {},
            'events':[],
            'id2painter': {}
        }
    
    id = int(row['cid'])
    cbdb_dao = CBDBDAO('latest.db', use_cache=True)
    cbdb_dao.getCBDBID(id)
    # 一度亲属关系和有直接事件联系的人，这群人互相之间关联的事件
    events = cbdb_dao.get_all_assoc_data()

    # 有画作信息的画家
    painter = {int(r['cid']): [r['山水'],r['人物'],r['花鸟']] 
    for i,r in data_csv.iterrows() 
    if math.isnan(r['cid']) == False
    }
    # cbdb认为是画家的人
    painterList = cbdb_dao.get_all_painter()

    id2painter = {key: painter[key] for key in cbdb_dao.cbdbid2name if key in painter}
    for id in painterList:
        if id not in id2painter:
            id2painter[id] = []

    return {
        'id':id,
        'id2name': cbdb_dao.cbdbid2name,
        'events':events,
        'id2painter': id2painter
    }

def auinfoscore(pid):
    # 获取人的生卒年和评价得分
    result= {}
    with open("authorinfo/"+pid+".json","r",encoding="UTF8")as f:
        alist = json.load(f)
    for author in alist:
        if "cid" not in alist[author]:continue
        sql ="select c_name_chn,c_personid,c_birthyear,c_deathyear from BIOG_MAIN where c_personid = '"+str(alist[author]["cid"])+"'"
        out = select("latest.db",sql)
        if out: # 搜不到的人就不管了
            cinfo={
                "cid":out[0]["c_personid"],
                "birthyear":out[0]["c_birthyear"],
                "deathyear":out[0]["c_deathyear"],
                "score1":0,
                "score2":0,
                "score3":0
            }
            result[author]=cinfo
    return result

def yinzhang(pid):
    # 获取该画作的印章列表
    yzdf=pd.read_csv("authorinfo/yzres.csv",encoding="UTF8")

    df_this = yzdf[yzdf["pid"]==int(pid)]
    yzlist=[]
    # 印章截图地址和印章匹配图地址
    jtpath = "../../../jiaailing/data/ChinesePainting/yinzhang/{pid}.png"
    pppath = "../../../jiaailing/data/ChinesePainting/seals/{pid}.png"
    for i in range(len(df_this)):
        info = {
            "印章截图文件名":df_this["yinzhang_img"].values[i], 
            "印章截图":imgexists(jtpath.format(pid=df_this["yinzhang_img"].values[i])),
            "top1":{
                "印章匹配文件名":df_this["top1"].values[i], 
                "印章匹配图":imgexists(pppath.format(pid = df_this["top1"].values[i])),
                "印章作者":df_this["top1_作者"].values[i],
                "印章内容":df_this["top1_印章内容"].values[i],
            },
            "top2":{
                "印章匹配文件名":df_this["top2"].values[i],
                "印章匹配图":imgexists(pppath.format(pid = df_this["top2"].values[i])),
                "印章作者":df_this["top2_作者"].values[i],
                "印章内容":df_this["top2_印章内容"].values[i],
            },
            "top3":{
                "印章匹配文件名":df_this["top3"].values[i],
                "印章匹配图":imgexists(pppath.format(pid = df_this["top3"].values[i])),
                "印章作者":df_this["top3_作者"].values[i],
                "印章内容":df_this["top3_印章内容"].values[i],
            },
            "top4":{
                "印章匹配文件名":df_this["top4"].values[i],
                "印章匹配图":imgexists(pppath.format(pid = df_this["top4"].values[i])),
                "印章作者":df_this["top4_作者"].values[i],
                "印章内容":df_this["top4_印章内容"].values[i],
            },
            "top5":{
                "印章匹配文件名":df_this["top5"].values[i],
                "印章匹配图":imgexists(pppath.format(pid = df_this["top5"].values[i])),
                "印章作者":df_this["top5_作者"].values[i],
                "印章内容":df_this["top5_印章内容"].values[i],
            }
        }
        yzlist.append(info)
    # print(yzlist[:10])
    return yzlist

def painting(pid):
    # 返回画作原图
    # 根据pid找paintingID
    yzdf=pd.read_csv("authorinfo/yzres.csv",encoding="UTF8")
    ppid = yzdf[yzdf["pid"]==int(pid)]["paintingID"].values[0]
    # print(ppid)
    fullpath = "../../../jiaailing/data/ChinesePainting/juan_changtu_height1000_chang9000yishang/{ppid}.jpg".format(ppid=ppid)
    img = imgexists(fullpath)
    return img

def coor(x,y):
    with open("reverse.json","r")as f:
        data=json.load(f)
    return data[x][y]

if __name__ == '__main__':
    coor(1,2)


    
