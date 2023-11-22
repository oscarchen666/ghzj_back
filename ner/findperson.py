# import hanlp
import pandas as pd
# import sqlite3
from tool import select,delauname,JsonEncoder,ddbc_name2aid,ddbc_personinfo,ddbc_place
from ner.getresulthc import infer #单独运行该文件时注释掉这两行,换下两行
from ner.dealsent import getsentences,predealh
# from getresulthc import infer
# from dealsent import getsentences,predealh
dbpath = "data/latest.db"

'''
对实体识别的时间地点人物进行矫正
目前只能指定按orig/里的格式输入
如果要别的方式如果再联系我再改吧
'''

def mytok(word):
    # 滑窗分词
    outlist=[]
    wlen=len(word)
    for fenlen in range(2,wlen):
        for i in range(0,wlen-fenlen+1):
            out = [word[i:i+fenlen],i,i+fenlen]
            outlist.append(out)
    return outlist

def findperson(info,dy):
    # 查询人名或别名
    sql_str ="select c_personid,c_name_chn,c_dy from BIOG_MAIN \
        where c_name_chn = '"+info["span"]+"' \
        or c_personid in (select c_personid from ALTNAME_DATA \
            where c_alt_name_chn=  '"+info["span"]+"')"
    output = select(dbpath,sql_str)
    # 查询aid，查不到为0

    if len(output)!=0:
        # 默认第一个结果，如果后续有同朝代的结果优先取同朝代的
        info["type"] = "PersonName"
        info["cid"] = output[0]["c_personid"]
        info["name"] = output[0]["c_name_chn"]
        for out in output:
            if out["c_dy"]==dy:
                info["cid"] = out["c_personid"]
                info["name"] = out["c_name_chn"]
                break
    elif info["span"] in ddbc_name2aid:#cbdb查不到但是ddbc查的到
        aid = ddbc_name2aid[info["span"]][0]
        info["type"] = "PersonName"
        info["cid"] = "unknow"
        info["name"] = ddbc_personinfo[aid]["name"]
    else: #如果整体人名查找不到，尝试分词后查找
        fens = mytok(info["span"])
        # print(fens)
        start = info["start"]
        for word, begin, end in fens: # 会保存分词后的最后一个查询成功词
            sql_str1 ="select c_personid,c_name_chn,c_dy from BIOG_MAIN \
                where c_name_chn = '"+word+"' or c_personid in \
                (select c_personid from ALTNAME_DATA \
                where c_alt_name_chn=  '"+word+"')"
            output1=select(dbpath,sql_str1)
            if len(output1)!=0:#需要修改span范围和文本并记录cid和name
                info["type"] = "PersonName"
                info["span"] = word
                info["start"] = start+begin
                info["end"] = start+end
                info["cid"] = output1[0]["c_personid"]
                info["name"] = output1[0]["c_name_chn"]
                for out in output1:
                    if out["c_dy"]==dy:
                        info["cid"] = out["c_personid"]
                        info["name"] = out["c_name_chn"]
                        break
            elif word in ddbc_name2aid:#cbdb查不到但是ddbc查的到
                aid = ddbc_name2aid[word][0]
                info["type"] = "PersonName"
                info["span"] = word
                info["start"] = start+begin
                info["end"] = start+end
                info["cid"] = "unknow"
                info["name"] = ddbc_personinfo[aid]["name"]
    if info["type"] == "PersonName":
        if info["span"] in ddbc_name2aid:#ddbc中取第一个
            info["aid"] =ddbc_name2aid[info["span"]][0]
        else:info["aid"] ="unknow"        
    return info

def findlocation(info):
    ddbc_place
    places = ddbc_place[ddbc_place["地名"]==info["span"]]
    if len(places)>0:
        info["type"] = "LocationName"
        info["aid"] = places["id"].values[0]
    sql="select c_addr_id,c_name_chn\
            from ADDRESSES where c_name_chn='{}'".format(info["span"])
    outs= select("",sql)
    if outs:
        info["type"] = "LocationName"
        info["cid"] = outs[0]["c_addr_id"]
    if info["type"] != "LocationName":
        # 直接查不到，分词查
        fens= mytok(info["span"])
        start = info["start"]
        for word, begin, end in fens:
            places = ddbc_place[ddbc_place["地名"]==word]
            if len(places)>0:
                info["type"] = "LocationName"
                info["aid"] = places["id"].values[0]
            sql="select c_addr_id,c_name_chn\
                    from ADDRESSES where c_name_chn = '{}'".format(word)
            outs= select("",sql)
            if outs:
                info["type"] = "LocationName"
                info["cid"] = outs[0]["c_addr_id"]
            if info["type"] == "LocationName":#匹配到了，修改
                info["span"] = word
                info["start"] = start+begin
                info["end"] = start+end
    return info
    print(info)

def searchfen(data):

    new_data = {}
    new_data["filefroms"] = data["filefroms"]
    newsents = []
    for sentence in data["sentences"]:
        newout={}
        sent=[]
        sentence["author"]=delauname(sentence["author"])
        dysql = "select c_personid ,c_dy from BIOG_MAIN where c_name_chn= '{}'".format(sentence["author"])
        output=select(dbpath,dysql)
        if len(output)!=0:
            dy=output[0]["c_dy"]
            newout["authorcid"] = output[0]["c_personid"]
        else:
            dy=-1
            newout["authorcid"] = "unknow"
        # 查询aid，查不到为0
        aid = ddbc_name2aid[sentence["author"]][0] if sentence["author"] in ddbc_name2aid else "unknow"
        newout["authoraid"]=aid
        for info in sentence["output"]:
            if info["type"]=='Person':
                info = findperson(info,dy)
            if info["type"]=="Location":
                info = findlocation(info)
            sent.append(info)
        
        newout["output"] = sent
        newout["sentence"] = sentence["sentence"]
        newout["author"] = sentence["author"]
        newsents.append(newout)

    new_data["sentences"]=newsents
    return new_data

if __name__ == '__main__':
    import json
    import os
    from tqdm import tqdm
    forisents = []
    dealsents = []
    authors=[]
    
    # 单文件预处理
    # filefroms = ["1035.json"]
    # filefroms = ["25.json", "91.json"]
    filelist = ["30000.json"]

    # 批量处理
    # df = pd.read_excel("data/paintinglist.xlsx")
    # pidlist = df["pid"].tolist()
    # filelist = [str(pid)+".json" for pid in pidlist]
    filefroms = []
    # 提取文件
    for file in filelist:
        if os.path.exists("nerresult/"+file):
            print(file+"有了")
            continue
        if file in ["1600.json","1602.json"]:continue
        # print(file)
        # exit()
        ss,author = getsentences("orig/"+file)
        authors.append(author)
        forisents.append(ss)
        dealsent = predealh(ss,limit=500)#分句上限，不能超过512，超过模型就炸了
        dealsents.append(dealsent)
        filefroms.append(file)

    # 模型推断
    # results = infer(forisents,dealsents,filefroms,authors)
    # # print(results)
    # for result in tqdm(results):
    #     new_data = searchfen(result)
    #     filefrom = new_data["filefroms"]
    #     with open(f"nerresult/{filefrom}","w",encoding="UTF8")as f:
    #         json.dump(new_data, f,indent=2, ensure_ascii=False,cls=JsonEncoder)
    for forisent,dealsent,filefrom,author in tqdm(zip(forisents,dealsents,filefroms,authors),total=len(forisents)):
        result = infer([forisent],[dealsent],[filefrom],[author])
        new_data = searchfen(result[0])
        filefrom = new_data["filefroms"]
        # print(filefrom)
        with open(f"nerresult/{filefrom}","w",encoding="UTF8")as f:
            json.dump(new_data, f,indent=2, ensure_ascii=False,cls=JsonEncoder)
        # continue

