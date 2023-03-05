import hanlp
import pandas as pd
import sqlite3
from ner.getresulthc import infer,JsonEncoder
from ner.dealsent import getsentences,predealh
dbpath = "latest.db"

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
    sql_str ="select c_personid,c_name_chn,c_dy from BIOG_MAIN where c_name_chn = '"+info["span"]+"' or c_personid in (select c_personid from ALTNAME_DATA where c_alt_name_chn=  '"+info["span"]+"')"
    output = select(dbpath,sql_str)

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
    
    else: #如果整体人名查找不到，尝试分词后查找
        fens = mytok(info["span"])
        # print(fens)
        start = info["start"]
        for word, begin, end in fens: # 会保存分词后的最后一个查询成功词
            sql_str1 ="select c_personid,c_name_chn,c_dy from BIOG_MAIN where c_name_chn = '"+word+"' or c_personid in (select c_personid from ALTNAME_DATA where c_alt_name_chn=  '"+word+"')"
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
            
    return info

def searchfen(data):

    new_data = {}
    new_data["filefroms"] = data["filefroms"]
    newsents = []
    for sentence in data["sentences"]:
        newout={}
        sent=[]
        dysql = "select c_personid ,c_dy from BIOG_MAIN where c_name_chn= '"+sentence["author"]+"'"
        output=select(dbpath,dysql)
        if len(output)!=0:
            dy=output[0]["c_dy"]
            newout["authorcid"] = output[0]["c_personid"]
        else:
            dy=-1
            newout["authorcid"] = "null"
        for info in sentence["output"]:
            if info["type"]=='Person':
                info = findperson(info,dy)

            sent.append(info)
        
        newout["output"] = sent
        newout["sentence"] = sentence["sentence"]
        newout["author"] = sentence["author"]
        newsents.append(newout)

    new_data["sentences"]=newsents
    return new_data

if __name__ == '__main__':
    import json
    forisents = []
    dealsents = []
    authors=[]

    # 单文件预处理
    # filefroms = ["1035.json"]
    filefroms = ["6.json"]
    # filefroms = ["23.json"]
    for file in filefroms:
        ss,author = getsentences("orig/"+file)
        authors.append(author)
        forisents.append(ss)
        dealsents.append(predealh(ss))
    results = infer(forisents,dealsents,filefroms,authors)

    new_data = searchfen(results[0])

    with open("nerresult/6.json","w",encoding="UTF8")as f:
        json.dump(new_data, f,indent=2, ensure_ascii=False,cls=JsonEncoder)

