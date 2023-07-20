from tqdm import tqdm
import time
import numpy as np
from ner.dealsent import * # 单独运行该文件时，注释掉该句，改用下面这句
# from dealsent import *
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

'''
调用Raner识别句子中的实体
'''
# 加载模型
ner_pipeline = pipeline(Tasks.named_entity_recognition, 'damo/nlp_raner_named-entity-recognition_chinese-base-literature')

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
    # 写文件函数
    for result in results:
        file_path = root+"/"+result["filefroms"]
        with open(file_path, "w",encoding="UTF8") as f:
            json.dump(result,f, indent=2,sort_keys=True, ensure_ascii=False,cls=JsonEncoder)

def infer(forisents,dealsents,filefroms,authors):
    # 推断
    # print("infering...")
    # print(len(filefroms))    
    results = []
    start=time.time()
    for oneforisent,onedealsent,filefrom,oneauthor in zip(forisents,dealsents,filefroms,authors):
        # 循环每一个文件
        allinfo={}
        allsen = []
        for forisent,dealsent,author in zip(oneforisent,onedealsent,oneauthor):
            # 循环文件中每一个句子
            # print(oneforisent)
            # print(onedealsent)
            if len(dealsent)==0:#原句小于126,直接处理
                out = ner_pipeline(forisent) # out是预测的实体结果
                out["sentence"] = forisent # 记录一下原句
                out["author"] = author 
                allsen.append(out)
            else:# 原句大于126
                foriouts = []
                # 每一个短句预测一次
                for dsent in dealsent:
                    foriout = ner_pipeline(dsent)
                    foriouts.append(foriout)
                # 投票产生最终结果
                out = toupiao(foriouts,forisent,dealsent)
                out["author"] = author
                allsen.append(out)
            allinfo["filefroms"] = filefrom # 记录一下源文件名字
            

        allinfo["sentences"] = allsen
        results.append(allinfo)
    # print(time.time()-start,"s")
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
        #循环每一个短句的结果
        for mm in foriouts[i]["output"]:
            # 循环每一个命名实体
            mm["start"]=mm["start"]+biaslist[i]
            mm["end"]=mm["end"]+biaslist[i]
            flag = str(mm["start"])+mm["type"]+str(mm["end"])#用位置+类别组合标识这个词
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
        #循环每一个标识
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
    filefroms = ["14393.json"]
    # filefroms = ["23.json"]
    for file in filefroms:
        ss,author = getsentences("orig/"+file)
        authors.append(author)
        forisents.append(ss)
        dealsents.append(predealh(ss,126))#可以在这里调整分句上限
    results = infer(forisents,dealsents,filefroms,authors)
    write_file(results,"nerresult")#写文件
    # print(results)
