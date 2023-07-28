import json
import os
import math
import pandas as pd
import math

from data.datadeal import *
from tool import *
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

def paintinglist():
    # 获取全部画作列表
    df1 = pd.read_excel("data/paintinglist.xlsx")
    df2 = pd.read_excel("authorinfo/pid_author.xlsx")
    plist = []
    for _,row in df1.iterrows():
        pid = row["pid"]
        thisdf2 = df2[df2["ID"]==pid]
        author = thisdf2["作者"].values[0]
        if pd.notna(author):
            author = str(author).split(",")[0]
            author = delauname(author)
        else:
            author = "unknow"
        cid = thisdf2["cid"].values[0]
        ## 查询cid
        # sql = f"select c_personid from biog_main where \
        #         c_name_chn = '{author}'"
        # out = select("",sql)
        # if out:
        #     cid = out[0]["c_personid"]
        #     df2.at[thisdf2.index,"cid"] = cid
        # else:
        #     cid = "unknow"
        #     df2.at[thisdf2.index,"cid"] = "unknow"
        plist.append({
            "paintingname":row["品名"],
            "pid":row["pid"],
            "id":row["work_id"],
            "author":author,
            "cid":cid
        })
    # df2.to_excel("authorinfo/pid_author2.xlsx",index=False)
    return plist


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
        sentence["author"] = delauname(sentence["author"])
        authorlist.append(sentence["author"])
        for span in sentence["output"]:
            if span["type"]=="PersonName": #人名直接使用题跋里的名字，无论原名别名
                if span["span"]in plist:
                    plist[span["span"]]=plist[span["span"]]+1
                else:
                    plist[span["span"]]=1
            elif span["type"]=="Location" or span["type"]=="LocationName":
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

def aullistbydy(oldres,pid):
    # 把作者列表转为按朝代分类并添加印章坐标信息
    dylist=list(set([oldres[au]["朝代"] for au in oldres]))
    newres={
        "dylist":dylist,
        "aulist":{dy:[] for dy in dylist}
    }
    yzaudf = pd.read_excel("authorinfo/yzres.xlsx")
    yzaudf = yzaudf[yzaudf["pid"]==int(pid)]
    yzaudf['处理人名'] = yzaudf['top1_作者'].apply(delauname) 
    for au in oldres:
        yzdf = yzaudf[yzaudf["处理人名"]==au]
        yzlist=[
            {"file": row["yinzhang_img"],"indx":row["indx"],"indy":row["indy"]}
            for _,row in yzdf.iterrows()
        ]
        info={
            "姓名":au,
            "本幅": int(oldres[au]["本幅"]),
            "总数": int(oldres[au]["总数"]),
            "cid":str(oldres[au]["cid"]),
            "aid":oldres[au]["aid"],
            "作者": oldres[au]["作者"],
            "印章列表":yzlist 
        }
        newres["aulist"][oldres[au]["朝代"]].append(info)
    return newres
    
def authorlist(pid):
    # 印章作者列表
    save_path = "authorinfo/"+str(pid)+".json"
    if os.path.exists(save_path):
        with open(save_path,"r",encoding="UTF8")as f:
            result = json.load(f)
        return aullistbydy(result,pid)
    
    yzdf = pd.read_excel("authorinfo/yzres.xlsx")
    with open("data/画作鉴藏统计5.json","r",encoding="UTF8") as f:
        jcdata = json.load(f)
    alist = list(yzdf[yzdf["pid"]==int(pid)]["top1_作者"].values)
    result = {}
    aulist = list(set(alist))
    for au in aulist:
        newau = delauname(au)
        if newau in jcdata:
            jczs = jcdata[newau]["印章清朝"]+jcdata[newau]["印章非清"]+jcdata[newau]["题跋清朝"]+jcdata[newau]["题跋非清"]
            # print(newau,jczs)
        else: jczs = int(alist.count(au))
        result[newau]={   
            # 需要将人名转为繁体，去掉()和·
            "本幅":int(alist.count(au)),
            "总数":jczs,
            "作者":"no"
            }
    # 题跋作者
    with open("nerresult/"+pid+".json","r",encoding="UTF8")as f:
        data = json.load(f)
    for sentence in data["sentences"]:
        sentence["author"]=delauname(sentence["author"])
        if sentence["author"] in result:
            result[sentence["author"]]["本幅"]=result[sentence["author"]]["本幅"]+1
            # result[sentence["author"]]["总数"]=result[sentence["author"]]["总数"]+1
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
    with open("data/dynasties.json", "r",encoding="utf8") as f:
        dyid2name=json.load(f)
        # 朝代代码转文字
    for au in result:
        
        sql = "select c_personid,c_dy from BIOG_MAIN \
            where c_name_chn = '{}' or \
            c_personid in (select c_personid from ALTNAME_DATA \
                where c_alt_name_chn=  '{}')" .format(au,au)
        out = select("data/latest.db",sql)

        result[au]["aid"]="unknow"
        result[au]["cid"]="unknow"
        result[au]["朝代"]="unknow"
        if au in ddbc_name2aid:#ddbc数据库
            aid=ddbc_name2aid[au][0]
            result[au]["aid"]=aid
            result[au]["朝代"]=ddbc_personinfo[aid]["dynasty"][0]
        if out:
            result[au]["朝代"]=dyid2name[str(out[0]["c_dy"])]
            result[au]["cid"]=out[0]["c_personid"]
            

    with open(save_path,"w",encoding="UTF8") as f:
        json.dump(result, f,indent=2, ensure_ascii=False)
        
    # 按朝代归类

    return aullistbydy(result,pid)

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
    yzdf=pd.read_excel("authorinfo/yzres.xlsx")

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

def changeyz(pid, yinzhang_imgs, change_yzids):
    # 修改印章匹配结果
    dfyz = pd.read_excel("authorinfo/yzres.xlsx")
    dfpp = pd.read_excel("data/印章信息表.xlsx")
    # print(dfpp[dfpp["ID"]==change_yzids[0]])
    # exit()
    ppidlist = dfpp["ID"].tolist()
    yzidlist = dfyz["yinzhang_img"].tolist()
    for yinzhang_img in yinzhang_imgs:
        if yinzhang_img not in yzidlist:
            return f"{yinzhang_img}印章序号不正确"
    for change_yzid in change_yzids:
        change_yzid=int(change_yzid)
        if change_yzid not in ppidlist:
            return f"{change_yzid}匹配序号不正确"
    for yinzhang_img, change_yzid in zip(yinzhang_imgs, change_yzids):
        change_yzid=int(change_yzid)
        dfthis = dfyz[dfyz["yinzhang_img"]==yinzhang_img]
        dfppthis = dfpp[dfpp["ID"]==change_yzid]
        # print(dfthis["pid"].values[0])
        if str(dfthis["pid"].values[0])!=pid:
            return f"{yinzhang_img}印章序号不属于画作{pid}"
        dfyz.loc[dfthis.index, "top1"] = str(change_yzid)
        # dfyz.loc[dfthis.index, "top1"] = dfyz.loc[dfthis.index, "top1"].astype(int)   
        dfyz.loc[dfthis.index, "top1_作者"] = dfppthis["名字"].values[0].rstrip()   
        dfyz.loc[dfthis.index, "top1_印章内容"] = dfppthis["左侧印章释文"].values[0].rstrip()  
        print(f"{pid}画作{yinzhang_img}印章top1修改成功！")

    # 将修改后的DataFrame写回到CSV文件  
    dfyz.to_excel("authorinfo/yzres.xlsx", index=False, encoding="UTF8")
    # 修改作者列表文件
    save_path = "authorinfo/"+pid+".json"
    if os.path.exists(save_path):
        os.remove(save_path)  
        print(f"文件 {save_path} 已成功删除")
    authorlist(pid)
    return f"{pid}画作修改成功！"

def image(imgid,imgtype):
    # 返回对应的图
    # 印章截图地址和印章匹配图地址
    # jtpath = "../../../jiaailing/data/ChinesePainting/yinzhang/{}"
    # pppath = "../../../jiaailing/data/ChinesePainting/seals/{}"
    # hxpath = "../../../jiaailing/data/ChinesePainting/seals_sslib_qiepian/{}"
    # hzpath = "../../../jiaailing/data/ChinesePainting/juan_changtu_height1000_chang9000yishang/{}"
    jtpath = "../../data/ChinesePainting/yinzhang/{}"
    pppath = "../../../../data/zw_12121193/seals/seal_koutu/{}"
    hxpath = "../../data/ChinesePainting/seals_sslib_qiepian/{}"
    hzpath = "../../data/ChinesePainting/juan_changtu_yuantu/{}"
    xtpath = "../../data/ChinesePainting/juan_seamcarving_changtu_seamcarving_4500x2_1000_fenge/{}"
    if imgtype=="截图" :
        fullpath = jtpath.format(imgid)
        print(fullpath)
        img = imgexists(fullpath)
    elif imgtype=="匹配":
        fullpath = pppath.format(imgid)
        print(fullpath)
        img = imgexists(fullpath)
    elif imgtype=="画作":
        # 根据pid找paintingID
        yzdf=pd.read_excel("authorinfo/pid_author.xlsx")
        ppid = yzdf[yzdf["ID"]==int(imgid)]["PaintingId"].values[0]
        fullpath = hzpath.format(ppid)
        print(fullpath)
        img = imgexists(fullpath)
    elif imgtype=="画心":
        fullpath = hxpath.format(imgid)
        print(fullpath)
        img = imgexists(fullpath)
    elif imgtype=="新图":
        yzdf=pd.read_excel("authorinfo/pid_author.xlsx")
        ppid = yzdf[yzdf["ID"]==int(imgid)]["PaintingId"].values[0]
        ppid1 = str(ppid)+"_1"
        fullpath1 = xtpath.format(ppid1)
        print(fullpath1)
        img1 = imgexists(fullpath1)
        ppid2 = str(ppid)+"_2"
        fullpath2 = xtpath.format(ppid2)
        print(fullpath2)
        img2 = imgexists(fullpath2)
        img = [img1,img2]
    return img

def coor(x,y):
    with open("data/reverse.json","r")as f:
        data=json.load(f)
    return data[x][y]

def huaxininfo(pid):
    # 获取画心数据
    hxdf = pd.read_excel("data/画心相似.xlsx")
    hxdf=hxdf[hxdf["ID"]==int(pid)]
    xshzid=hxdf["相似画作_ID"].values[0].split(";")
    xsimg=hxdf["相似画作图"].values[0].split(";")
    auname=hxdf["作者"].values[0].split(";")
    hzname=hxdf["品名"].values[0].split(";")
    xsscore=hxdf["分数"].values[0].split(";")
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
            cid="unknow"
            birday=None
            deaday=None
        info={
            "相似画作id":xshzid[i],
            "相似画作图":xsimg[i],
            "作者":au,
            "cid":cid,
            "作者生年":birday,
            "作者卒年":deaday,
            "画作名":cc.convert(hzname[i]),
            "相似度":xsscore[i],
            "相似类型":"画心相似"
        }
        result.append(info)
    wbdf = pd.read_excel("data/文本相似.xlsx")
    wbdf = wbdf[wbdf["ID"]==int(pid)]
    xshzid=wbdf["画作id"].values[0].split(";")
    xsimg=wbdf["画作链接"].values[0].split(";")
    auname=wbdf["画作作者"].values[0].split(";")
    hzname=wbdf["画作品名"].values[0].split(";")
    xsscore=wbdf["相似画作分数"].values[0].split(";")
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
            cid="unknow"
            birday=None
            deaday=None
        info={
            "相似画作id":xshzid[i],
            "相似画作图":xsimg[i],
            "作者":au,
            "cid":cid,
            "作者生年":birday,
            "作者卒年":deaday,
            "画作名":cc.convert(hzname[i]),
            "相似度":xsscore[i],
            "相似类型":"文本相似"
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
    newname2id = sort_name2id(name2id)
    result ={
        "关系列表":kinlist,
        "人物信息":tmpid2info,
        "人物列表":name2id,
        "排序人物列表":newname2id
    }
    # print(len(name2id))
    return result

def personscore(pid,cname2id):
    # 根据画作取所有人物的详细信息形成得分，支持新增人物
    cidlist=[]
    name2id = {}
    aulist={}
    with open("authorinfo/"+pid+".json","r",encoding="UTF8")as f:
        orinaulist = json.load(f)
    if pid!=reladto.tmppid_score or not cname2id:
        # 切换画作或者无新增人员但请求时，默认读取作者列表并清空存储信息
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
    with open("data/画作鉴藏统计5.json","r",encoding="UTF8")as f:
        hzjc=json.load(f)
    neres={}
    max_score=0
    min_score=100
    for cid in relares:
        ss = relares[cid]["分数"]
        auname=relares[cid]["姓名"]
        if auname not in hzjc:
            hzjc[auname]={"印章清朝": 0,"印章非清": 0,"题跋清朝": 0,"题跋非清": 1,"被鉴藏": 0,"画作数": 0}
        jcfq=hzjc[auname]["印章非清"]+hzjc[auname]["题跋非清"]
        jcq=hzjc[auname]["印章清朝"]+hzjc[auname]["题跋清朝"]
        # 鉴藏清朝画作0.4倍权重
        s1 = ss["画派"]+ round(math.log(jcfq+0.4*jcq+1)+math.log(hzjc[auname]["被鉴藏"]+1) 
                            + 5*math.log(hzjc[auname]["画作数"]+1))
        s2 = min(round(3.5*math.log(ss["古籍讨论"]+1)),36)
        s3 = ss["文人"]*10+ss["鉴藏家"]*10+ss["最高官职"]
        max_score=max(max_score,s1+s2+s3)
        min_score=min(min_score,s1+s2+s3)
        relares[cid]["分数"]={"画作相关":s1,"讨论度":s2,"身份":s3}
        relares[cid]["印章题跋数"]={
            "印章":hzjc[auname]["印章非清"]+hzjc[auname]["印章清朝"],
            "题跋":hzjc[auname]["题跋非清"]+hzjc[auname]["题跋清朝"]}
        # 从作者列表存储信息中读取部分数据
        relares[cid]["题跋印章总数"]=jcfq+jcq
        if auname in orinaulist:
            relares[cid]["作者"]=orinaulist[auname]["作者"]
            relares[cid]["题跋印章本幅"]=orinaulist[auname]["本幅"]
        else:
            relares[cid]["作者"]="no"
            relares[cid]["题跋印章本幅"]=0
        neres[cid]={}
        # neres[cid]["分数"]={"画作相关":s1,"讨论度":s2,"身份":s3} 
        neres[cid]["分数"]=s1+s2+s3
        neres[cid]["姓名"]=auname
        neres[cid]["生卒"]=(relares[cid]["生年"],relares[cid]["卒年"])
    result = {
        "人物关系信息":relares,
        "人物列表":name2id,
        "最高得分":max_score,
        "最低得分":min_score
    }
    # return neres
    return result

def onestringinfo(name,stype="cperson"):
    # 模糊查询名字
    res = []
    name=delauname(name)
    if stype == "cperson":
        cidlist=[]
        sql_str ="select c_personid from BIOG_MAIN \
            where c_name_chn like '%{}%' or c_personid in\
            (select c_personid from ALTNAME_DATA \
            where c_alt_name_chn like '%{}%')".format(name,name)
        output = select("",sql_str)
        if not output: return res
        for out in output:
            cidlist.append(out["c_personid"])
        tmpid2info = reladto.getid2info(cidlist)
        for cid in cidlist:
            sql = " select count(*) from assoc_data where c_personid = {}".format(cid)
            assoc_count=select("",sql)[0]["count(*)"]
            res.append({"id":cid,
                "name":tmpid2info[cid]["姓名"],
                "assoc_count":assoc_count,
                "birth":tmpid2info[cid]["生年"],
                "death":tmpid2info[cid]["卒年"],
                "altname":tmpid2info[cid]["别名"],
                "place":tmpid2info[cid]["籍贯"],
                "dynasty":tmpid2info[cid]["朝代"]})
    elif stype == "aperson":
        aidlist = []
        for ddbc_name in ddbc_name2aid:
            if name in ddbc_name:
                aidlist.extend(ddbc_name2aid[ddbc_name])
        print(len(aidlist))
        if not aidlist:return res
        # aidlist=ddbc_name2aid[personname]
        for aid in aidlist:
            info = ddbc_personinfo[aid]
            res.append({"id":aid,
                "name":info["name"],
                "birth":info["birth"][:5],
                "death":info["death"][:5],
                "altname":info["altname"],
                "place":info["place"],
                "dynasty":info["dynasty"][0]})
    elif stype== "cplace":
        sql="select c_addr_id,c_name_chn,belongs1_Name,belongs2_Name,belongs3_Name,belongs4_Name\
              from ADDRESSES where c_name_chn like '%{}%'".format(name)
        outs= select("",sql)
        if not outs: return res
        for out in outs:
            sql = "select c_alt_names from ADDR_CODES where c_addr_id = {}".format(out["c_addr_id"])
            altout=select("",sql)[0]
            p4= out["belongs4_Name"]+"-" if out["belongs4_Name"] else ""
            p3= out["belongs3_Name"]+"-" if out["belongs3_Name"] else ""
            p2= out["belongs2_Name"]+"-" if out["belongs2_Name"] else ""
            p1= out["belongs1_Name"] if out["belongs1_Name"] else ""
            place= p4+p3+p2+p1
            res.append({"id":out["c_addr_id"],"placename":out["c_name_chn"],
                        "location":place,"altname":altout["c_alt_names"]})

    elif stype == "aplace":
        places = ddbc_place[ddbc_place["地名"].str.contains(name, na=False)]
        for plid,plname,pllo in zip(places["id"],places["地名"],places["所在位置"]):
            if pd.isna(pllo) :pllo="unknow"
            res.append({"id":plid,"placename":plname,"location":pllo})
    elif stype == "time":
        res = dealyearstring(name)
    return res
    # print(res)

def cid2name(cid):
    sql="select c_name_chn from biog_main where c_personid = {}".format(cid)
    out=select("",sql)
    return out[0]["c_name_chn"]

def trytry():
    # df1 = pd.read_excel("data/paintinglist.xlsx")
    # personlist = []
    # for index,row in df1.iterrows():
    #     personlist.extend(row["全部人"].split(","))
    # personlist = list(set(personlist))
    # print(len(personlist))
    # spersonlist = []
    # for person in personlist:
    #     sql = f"select c_birthyear,c_deathyear from biog_main where c_name_chn = '{person}'"
    #     out=select("",sql)
    #     if out:
    #         if out[0]["c_birthyear"] or out[0]["c_deathyear"]:
    #              spersonlist.append(person)
    # print(len(spersonlist))
    # df2 = pd.read_excel("data\古籍讨论度new.xlsx")
    # hplist = df2["题跋人"].tolist()
    # for person in spersonlist:
    #     if person not in hplist:
    #         newrow= {"题跋人":person}
    #         df2 = df2.append(newrow, ignore_index=True)
    # df2.to_excel("data\古籍讨论度newnew.xlsx")         

        
    sql = "select * from biog_main where c_name_chn = '盧鴻'"
    out=select("",sql)
    print(out)
          
    

if __name__ == '__main__':
    # print(changeyz("101",["101_12__0"],[523]))
    paintinglist()
    # trytry()
    # print(yinzhang("894"))
    # print(onepernameinfo("孟頫",stype="aid"))


    
