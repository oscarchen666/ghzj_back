from tqdm import tqdm
import os
import time
import numpy as np
from ner.dealsent import *
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

class JsonEncoder(json.JSONEncoder):
    # 用于处理写json文件格式问题
    def default(self, obj):
        if isinstance(obj, (np.integer, np.floating, np.bool_)):
            return obj.item()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(JsonEncoder, self).default(obj)

def write_file(results,root):
    for result in results:
        file_path = root+"/"+result["filefroms"]
        with open(file_path, "w",encoding="UTF8") as f:
            json.dump(result,f, indent=2,sort_keys=True, ensure_ascii=False,cls=JsonEncoder)

def infer(forisents,dealsents,filefroms,authors):
    print(len(filefroms))
    ner_pipeline = pipeline(Tasks.named_entity_recognition, 'damo/nlp_raner_named-entity-recognition_chinese-base-literature')
    results = []
    start=time.time()
    for oneforisent,onedealsent,filefrom,oneauthor in zip(forisents,dealsents,filefroms,authors):
        # 一个文件中的所有句子
        allinfo={}
        allsen = []
        for forisent,dealsent,author in zip(oneforisent,onedealsent,oneauthor):
            if len(dealsent)==0:#原句小于126,直接处理
                out = ner_pipeline(forisent)
                out["sentence"] = forisent
                out["author"] = author
                allsen.append(out)
            else:#原句大于126
                foriouts = []
                
                for dsent in dealsent:
                    foriout = ner_pipeline(dsent)
                    foriouts.append(foriout)
                # 
                out = toupiao(foriouts,forisent,dealsent)
                out["author"] = author
                allsen.append(out)
            allinfo["filefroms"] = filefrom
            

        allinfo["sentences"] = allsen
        results.append(allinfo)
    print(time.time()-start,"s")
    return results

def toupiao(foriouts,forisent,dealsent):
    # 滑窗生成的一系列结果，用投票的方式得到最终结果
    chailist = forisent.split("。")[:-1]
    biaslist=[0] # 句子偏移，第一句偏移0
    for i in range(0,len(chailist)):
        biaslist.append(biaslist[i]+len(chailist[i])+1)
    # [0, 14, 23, 28, 38, 53, 57, 67, 74, 80, 87, 92, 100, 114, 121, 130, 136, 146, 158, 163, 168, 175, 182]

    countlist = {} # 统计相同的识别结果
    for i in range(len(foriouts)):
        for mm in foriouts[i]["output"]:
            mm["start"]=mm["start"]+biaslist[i]
            mm["end"]=mm["end"]+biaslist[i]
            flag = str(mm["start"])+mm["type"]+str(mm["end"])
            
            if flag not in countlist:
                mm["count"]=1
            else:
                mm["count"]=countlist[flag]["count"]+1
            countlist[flag]=mm
    # print(countlist)        
    lenlist = [len(deal) for deal in dealsent]
    out={}
    output = []
    for flag in countlist:
        oner=countlist[flag]
        insent=0
        for i in range(len(lenlist)):
            if biaslist[i]<=oner["start"] and oner["start"]<biaslist[i]+lenlist[i]:
                # 如果start在这个分句范围内，则整个词肯定在分句范围内
                insent=insent+1
        if insent==0:print("除0?:",oner)
        elif oner["count"]/insent>0.5: # 投票过半视为有效
            oner.pop("count")
            output.append(oner)
    output = sorted(output, key=lambda x: x["start"]) #排序
        
    out["output"]=output
    out["sentence"] = forisent
    return out

if __name__ == '__main__':

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
    write_file(results,"nerresult")
    # print(results)
