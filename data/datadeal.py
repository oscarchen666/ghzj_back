# 部分数据处理函数
import pandas as pd
import json
from tool import cc

def huapai():
    # 画派.xlsx-画派信息.json
    dj={"A":10,"B":8,"C":6,"D":4}
    bl=1.5
    df = pd.read_excel("data/画派.xlsx")
    res={}
    for i,r in df.iterrows():
        pj = dj[r["评级"].strip(" ")]
        if not pd.isnull(r["画派开创者"]):
            for ps in r["画派开创者"].split("、"):
                ps=cc.convert(ps)
                if ps not in res:
                    res[ps]=int(pj*bl)
                elif res[ps]<int(pj*bl):
                    res[ps]=int(pj*bl)
        if not pd.isnull(r["画派代表人物"]):            
            for ps in r["画派代表人物"].split("、"):
                ps=cc.convert(ps)
                if ps not in res:
                    res[ps]=pj
                elif res[ps]<pj:
                    res[ps]=pj
        with open("data/画派信息.json","w",encoding="UTF8")as f:
            json.dump(res,f,indent=2,ensure_ascii=False)

def gzpj():
    #官职品级
    with open("data/官职品级2.json", "r",encoding="UTF8") as f:
        data=json.load(f)
        f.close()
    # 假设你的json文件已经保存在一个变量名为data的字典中
    # 创建一个字典来存储品级和得分的对应关系
    grade_score = {"正一品": 18, "从一品": 17, "正二品": 16, "从二品": 15,
                "正三品": 14, "从三品": 13, "正四品": 12, "从四品": 11,
                "正五品": 10, "从五品": 9, "正六品": 8, "从六品":7,
                "正七品": 6, "从七品": 5, "正八品": 4, "从八品":3,
                "正九品": 2, "从九品": 1,"未详" : 0,"皇帝":20}
    # 皇帝得分仅作记录，因为不存在于任官事件中

    # 遍历data中的每个官职
    for office in data:
        # 获取官职的"品级"
        grade = data[office]["品级"][:3]
        # 根据grade_score字典获取对应的得分
        score = grade_score.get(grade)
        # 在data中为官职增加一个键名为“得分”的键值对
        data[office]["得分"] = score

    # 打印修改后的data
    with open("data/官职品级2.json", "w",encoding="UTF8") as f:
        json.dump(data,f,indent=2,ensure_ascii=False)