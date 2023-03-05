from ner.findperson import select
import pandas as pd
import opencc
import json

cc = opencc.OpenCC("s2t")
df = pd.read_excel("qhqs2.xlsx",)
# print(df["印章作者"].values)
all_res={}
for i in range(len(df["印章作者"].values)):
    name= cc.convert(df["印章作者"].values[i])
    name=name.split("（")[0]
    name=name.replace("·",'')
    sql = "select c_name_chn,c_dy from BIOG_MAIN where c_name_chn = '"+name+"' or c_personid in (select c_personid from ALTNAME_DATA where c_alt_name_chn=  '"+name+"')"
    out = select("latest.db",sql)
    res={
        "thisnum":str(df["印章在本幅卷中的个数"].values[i]),
        "allnum":str(df["鉴藏画作数量"].values[i]),
    }
    if out:
        res["dy"]=str(out[0]["c_dy"])
    all_res[name]=res
    # print(res)
with open("qhqszz2.json","w",encoding="UTF8")as f:
    json.dump(all_res, f,indent=2, ensure_ascii=False)
# word = cc.convert("子羽")
# sql = "select c_personid,c_name_chn,c_dy from BIOG_MAIN where c_name_chn = '"+word+"' or c_personid in (select c_personid from ALTNAME_DATA where c_alt_name_chn=  '"+word+"')"
# print(select("latest.db",sql))