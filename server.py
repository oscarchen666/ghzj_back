import json
import os
import math
import pandas as pd
import math

from data.datadeal import *
from tool import imgexists,select,delauname,JsonEncoder,cc
from assoc.RelaDto import reladto

def ner_search(pid):
    # ner生成并搜索    
    from ner.getresulthc import infer
    from ner.dealsent import getsentences,predealh
    from ner.findperson import searchfen
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

def aullistbydy(oldres):
    # 把作者列表转为按朝代分类
    dylist=list(set([oldres[au]["朝代"] for au in oldres]))
    newres={
        "dylist":dylist,
        "aulist":{dy:[] for dy in dylist}
    }
    for au in oldres:
        info={
            "姓名":au,
            "本幅": int(oldres[au]["本幅"]),
            "总数": int(oldres[au]["总数"]),
            "cid":str(oldres[au]["cid"]),
            "作者": oldres[au]["作者"]
        }
        newres["aulist"][oldres[au]["朝代"]].append(info)
    return newres
    
def authorlist(pid):
    # 印章作者列表
    save_path = "authorinfo/"+pid+".json"
    if os.path.exists(save_path):
        with open(save_path,"r",encoding="UTF8")as f:
            result = json.load(f)
        return aullistbydy(result)
    
    yzdf = pd.read_csv("authorinfo/yzres.csv",encoding="UTF8")
    audf = pd.read_excel("authorinfo/人物的鉴藏画作个数.xlsx")
    alist = list(yzdf[yzdf["pid"]==int(pid)]["top1_作者"].values)
    result = {}
    aulist = list(set(alist))
    for au in aulist:
        result[delauname(au)]={   
            # 需要将人名转为繁体，去掉()和·
            "本幅":int(alist.count(au)),
            "总数":int(audf[audf["top1_作者"]==au]["鉴藏画作数量"].values[0]),
            "作者":"no"
            }
    # 题跋作者
    with open("nerresult/"+pid+".json","r",encoding="UTF8")as f:
        data = json.load(f)
    for sentence in data["sentences"]:
        sentence["author"]=delauname(sentence["author"])
        if sentence["author"] in result:
            result[sentence["author"]]["本幅"]=result[sentence["author"]]["本幅"]+1
            result[sentence["author"]]["总数"]=result[sentence["author"]]["总数"]+1
        else:
            result[sentence["author"]]={"本幅":1,"总数":1,"作者":"no"}

    # 画作作者
    hzdf=pd.read_excel("authorinfo/pid_author.xlsx").fillna(value="佚名")
    hzau=cc.convert(hzdf[hzdf["ID"]==int(pid)]["作者"].values[0])
    if hzau not in result:
        result[hzau]={"本幅": 0,"总数": 0,"作者":"yes"}
    else:
        result[hzau]["作者"]="yes"
    # 查询朝代和cid
    with open("authorinfo/id2dy.json","r",encoding="UTF8")as f:
        id2dy=json.load(f)
        # 朝代代码转文字
    for au in result:
        
        sql = "select c_personid,c_dy from BIOG_MAIN where c_name_chn = '"+au+"' or c_personid in (select c_personid from ALTNAME_DATA where c_alt_name_chn=  '"+au+"')" 
        out = select("data/latest.db",sql)
        if out:
            result[au]["朝代"]=str(out[0]["c_dy"])
            result[au]["cid"]=out[0]["c_personid"]
        else:
            result[au]["朝代"]="unknow"
            result[au]["cid"]="unknow"

    with open(save_path,"w",encoding="UTF8") as f:
        json.dump(result, f,indent=2, ensure_ascii=False)
        
    # 按朝代归类

    return aullistbydy(result)

def lianxian(pid,name):
    # 作者和词云、图像连线
    # 和词云连线
    cylines = []
    if name=="愛新覺羅弘曆": name="清高宗"
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

def auinfoscore(pid):
    # 获取人的生卒年和评价得分等信息
    result= {}
    with open("authorinfo/"+pid+".json","r",encoding="UTF8")as f:
        alist = json.load(f)
    
    for author in alist:
        if alist[author]["cid"]=="unknow":continue
        sql ="select c_name_chn,c_personid,c_birthyear,c_deathyear from BIOG_MAIN where c_personid = '"+str(alist[author]["cid"])+"'"
        out = select("data/latest.db",sql)
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
    yzaulist=list(set(df_this["top1_作者"].values))
    yzlist={delauname(yzau):[]for yzau in yzaulist}
    
    for i in range(len(df_this)):
        info = {
            "印章截图地址":df_this["yinzhang_img"].values[i],
            "top1":{
                "印章匹配图地址":df_this["top1"].values[i],
                "印章作者":delauname(df_this["top1_作者"].values[i]),
                "印章内容":str(df_this["top1_印章内容"].values[i]),
            },
            "top2":{
                "印章匹配图地址":df_this["top2"].values[i],
                "印章作者":delauname(df_this["top2_作者"].values[i]),
                "印章内容":str(df_this["top2_印章内容"].values[i]),
            },
            "top3":{
                "印章匹配图地址":df_this["top3"].values[i],
                "印章作者":delauname(df_this["top3_作者"].values[i]),
                "印章内容":str(df_this["top3_印章内容"].values[i]),
            },
            "top4":{
                "印章匹配图地址":df_this["top4"].values[i],
                "印章作者":delauname(df_this["top4_作者"].values[i]),
                "印章内容":str(df_this["top4_印章内容"].values[i]),
            },
            "top5":{
                "印章匹配图地址": df_this["top5"].values[i],
                "印章作者":delauname(df_this["top5_作者"].values[i]),
                "印章内容":str(df_this["top5_印章内容"].values[i]),
            }
        }
        yzlist[delauname(df_this["top1_作者"].values[i])].append(info)
    # print(yzlist[:10])
    return yzlist

def image(imgid,imgtype):
    # 返回对应的图
    # 印章截图地址和印章匹配图地址
    jtpath = "../../../jiaailing/data/ChinesePainting/yinzhang/{imgid}"
    pppath = "../../../jiaailing/data/ChinesePainting/seals/{imgid}"
    hxpath = "../../../jiaailing/data/ChinesePainting/seals_sslib_qiepian/{imgid}"
    hzpath = "../../../jiaailing/data/ChinesePainting/juan_changtu_height1000_chang9000yishang/{ppid}"
    if imgtype=="截图" :fullpath = jtpath.format(imgid=imgid)
    elif imgtype=="匹配":fullpath = pppath.format(imgid=imgid)
    elif imgtype=="画作":
        # 根据pid找paintingID
        yzdf=pd.read_csv("authorinfo/yzres.csv",encoding="UTF8")
        ppid = yzdf[yzdf["pid"]==int(imgid)]["paintingID"].values[0]
        fullpath = hzpath.format(ppid=ppid)
    elif imgtype=="画心":fullpath = hxpath.format(imgid=imgid)
    print(fullpath)
    img = imgexists(fullpath)
    return img

def coor(x,y):
    with open("data/reverse.json","r")as f:
        data=json.load(f)
    return data[x][y]

def huaxininfo(pid):
    # 获取画心数据
    hxdf = pd.read_excel("data/画心.xlsx")
    hxdf=hxdf[hxdf["ID"]==int(pid)]
    xshzid=hxdf["相似画作_ID"].values[0].split(",")
    xsimg=hxdf["相似画作图"].values[0].split(",")
    auname=hxdf["作者"].values[0].split(",")
    hzname=hxdf["品名"].values[0].split(",")
    result = []
    for i in range(len(xshzid)):
        # 作者生卒年
        au = cc.convert(auname[i])
        sql = "select c_personid,c_birthyear,c_deathyear \
                from biog_main where c_name_chn = '{}'".format(au)
        out = select("data/latest.db",sql)
        if out:
            cid = out[0]["c_personid"]
            birday = out[0]["c_birthyear"]
            deaday = out[0]["c_deathyear"]
        else:
            cid="unknown"
            birday=None
            deaday=None
        info={
            "相似画作id":xshzid[i],
            "相似画作图":xsimg[i],
            "作者":au,
            "cid":cid,
            "作者生年":birday,
            "作者卒年":deaday,
            "画作名":hzname[i]
        }
        result.append(info)
    return result
    
def personnet(cid):
    # 查询和该人物相关的关系图谱
    result= reladto.select_one_person(cid)
    return result

def personmatrix(pid,cname2id):
    # 根据画作取所有人物的详细信息形成矩阵，支持新增人物
    cidlist=[]
    name2id = {}
    aulist={}
    if pid!=reladto.tmppid_matrix or not cname2id:
        # 切换画作或者无新增人员但请求时，默认读取作者列表并清空存储信息
        with open("authorinfo/"+pid+".json","r",encoding="UTF8")as f:
            aulist = json.load(f)
        aulist = {au:aulist[au]["cid"]for au in aulist}
    else:
        # 临时存储的人物列表，可能包括上次请求手动添加的人物
        aulist = reladto.tmplist_matrix 
    aulist.update(cname2id)  
    for au in aulist:
        # 人名列表包括所有作者，但是cbdb查不到的人不会有关系数据和个人信息
        name2id[au]=aulist[au]
        if aulist[au]!="unknow":
            cidlist.append(aulist[au])
    # 存储当前pid和人物列表
    reladto.tmppid_matrix=pid
    reladto.tmplist_matrix=aulist
    # print(aulist)
    
    # 查询人物信息
    tmpid2info=reladto.getid2info(cidlist)
    
    # 三种关系查询：亲缘、关系、任官
    kinlist=reladto.select_kin(cidlist)
    assoclist=reladto.select_assoc(cidlist)
    officelist = reladto.select_office(cidlist)
    kinlist.extend(assoclist)
    kinlist.extend(officelist)
    result ={
        "关系列表":kinlist,
        "人物信息":tmpid2info,
        "人物列表":name2id
    }
    # print(len(name2id))
    return result


def personscore(pid,cname2id):
    # 根据画作取所有人物的详细信息形成得分，支持新增人物
    cidlist=[]
    name2id = {}
    aulist={}
    if pid!=reladto.tmppid_score or not cname2id:
        # 切换画作或者无新增人员但请求时，默认读取作者列表并清空存储信息
        with open("authorinfo/"+pid+".json","r",encoding="UTF8")as f:
            orinaulist = json.load(f)
        aulist = {au:orinaulist[au]["cid"]for au in orinaulist}
    else:
        # 临时存储的人物列表，可能包括上次请求手动添加的人物
        aulist = reladto.tmplist_socre
    aulist.update(cname2id) 
    for au in aulist:
        # 人名列表包括所有作者，但是cbdb查不到的人不会有关系数据和个人信息
        name2id[au]=aulist[au]
        if aulist[au]!="unknow":
            cidlist.append(aulist[au])
    # 存储当前pid和人物列表
    reladto.tmppid_score=pid
    reladto.tmplist_socre=aulist
    # 查询人物信息和关系
    relares = reladto.count_rela(cidlist)
    # 读取画作鉴藏统计
    with open("data/画作鉴藏统计.json","r",encoding="UTF8")as f:
        hzjc=json.load(f)
    for cid in relares:
        ss = relares[cid]["分数"]
        auname=relares[cid]["姓名"]
        if auname not in hzjc:
            hzjc[auname]={"鉴藏": 0,"被鉴藏": 0,"画作数": 0}
        s1 = ss["画派"]+ round(math.log(hzjc[auname]["鉴藏"]+1) + math.log(hzjc[auname]["被鉴藏"]+1) + 5*math.log(hzjc[auname]["画作数"]+1))
        s2 = round(3.5*math.log(ss["古籍讨论"]+1))
        s3 = ss["文人"]*10+ss["鉴藏家"]*10+ss["最高官职"]
        relares[cid]["分数"]={"画作相关":s1,"讨论度":s2,"身份":s3} 
        
    result = {
        "人物关系信息":relares,
        "人物列表":name2id
    }

    return result


def trytry():
    huapai()
    

if __name__ == '__main__':
    trytry()


    
