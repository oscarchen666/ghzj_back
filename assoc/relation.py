from tool import select
import json

# 这个文件是用于提取cbdb中的各种关系，并按需求归类（政治、文学、社交、亲缘、画作、其他）
# 该版的cbdb的0级关系类别包括：社会、学术、朋友、政治、著述、军事、医疗、宗教、家庭（无血缘）、财务
# 其中本项目单独需要抽取部分小类作为画作类
# cbdb每个关系有一个关系小类，关系小类从属于一个1级关系类，1级关系类从属于一个0级关系类，前前后后分了四张表，离谱

sql = "select assoc_codes.c_assoc_code,assoc_types.c_assoc_type_id,c_assoc_desc_chn,c_assoc_type_desc_chn,c_assoc_type_parent_id\
        from assoc_codes,assoc_code_type_rel,assoc_types\
        where assoc_codes.c_assoc_code=assoc_code_type_rel.c_assoc_code\
        and assoc_code_type_rel.c_assoc_type_id = assoc_types.c_assoc_type_id"
outs = select("latest.db",sql)
rela={out['c_assoc_code']:
            {"关系描述":out['c_assoc_desc_chn'],
             "cbdb类型id":out['c_assoc_type_id'],
            "cbdb关系类型":out['c_assoc_type_desc_chn'],
            "cbdb关系上级":out['c_assoc_type_parent_id']} 
        for out in outs}

# 关系需求文件
with open("assoctype.json","r",encoding="UTF8")as f:
    data = json.load(f)

for tid in rela:
    sql="select c_assoc_type_desc_chn from assoc_types\
        where c_assoc_type_id ='"+rela[tid]["cbdb关系上级"]+"'"
    outs = select("latest.db",sql)
    rela[tid]["cbdb关系上级"]=outs[0]["c_assoc_type_desc_chn"]#把0级类别的id换成类别描述

    if rela[tid]["关系描述"] in data:#小类从属画作
        rela[tid]["关系类型"] = data[rela[tid]["关系描述"]]
    elif rela[tid]["cbdb关系上级"] in data:
        rela[tid]["关系类型"] = data[rela[tid]["cbdb关系上级"]]

with open("id2rela.json","w",encoding="UTF8") as f:
    json.dump(rela,f,indent=2, ensure_ascii=False)
# print(len(outs))
# for out in outs[:20]:
#     print(out)