from tool import select
import json
import pandas as pd
import opencc
from functools import cmp_to_key
cc = opencc.OpenCC("t2s")

# 如果你很不幸需要修改这部分代码，我的建议是重写一遍，这部分写的又臭又长，我自己都不想看
# 相比而言cbdb还是好懂的。不如看看相关联的json和xlsx文件，可能还有点用
# 因为这部分就是别人写的我也看不下去干脆自己重写了。

class RelaDto():
    # 该类用于查询人物信息以及人物关系
    def __init__(self,path="data/latest.db"):
        self.dbpath = path
        self.tmplist_matrix = {} # 临时人物列表
        self.tmplist_socre = {}
        self.tmppid_matrix = -1 # 临时记录画作id
        self.tmppid_score = -1
        # 关系id转关系名和类别
        with open ("data/id2rela.json","r",encoding="UTF8")as f:
            self.id2rela = json.load(f)
        with open ("data/dynasties.json","r",encoding="UTF8")as f:
            self.id2dy = json.load(f)
        painterlist=pd.read_excel("data/painter.xlsx")
        self.painterlist=painterlist["authorNameTC"].to_list()

    def getid2info(self,cidlist):
        # 获取人物列表的cid-信息对
        tmpid2info={}

        with open("data/官职品级2.json","r",encoding="UTF8")as f:
            gzpj=json.load(f)
        
        sql = "select c_personid,c_name_chn,c_birthyear,c_deathyear,c_index_addr_id,c_dy\
              from biog_main where c_personid in {}"
        sql=sql.format(tuple(cidlist) if len(cidlist) > 1 else "({})".format(cidlist[0]))
        outs = select(self.dbpath,sql)
        for out in outs:
            cid = out["c_personid"]
            #别名
            sql="select c_alt_name_chn from altname_data\
                where c_personid = {}".format(cid)
            outs1 = select(self.dbpath,sql)
            bmlist=[out1["c_alt_name_chn"]for out1 in outs1]
            # 籍贯
            if out["c_index_addr_id"]!=None:
                sql="select c_name_chn from addr_codes\
                        where c_addr_id={}".format(out["c_index_addr_id"])
                outs2 = select(self.dbpath,sql)
                jg=outs2[0]["c_name_chn"]
            else: jg=None
            # 朝代
            if not out["c_dy"]:dynasty="unknow"
            else:dynasty=self.id2dy[str(out["c_dy"])]
            # 社会区分
            sql = "select status_codes.c_status_code,c_status_desc_chn from status_data,status_codes\
                    where status_data.c_status_code=status_codes.c_status_code\
                    and c_personid = {}".format(cid)
            outs3 = select(self.dbpath,sql)
            shlist=None#避免没有社会分区报错
            shidlist=[]
            if outs3: 
                shlist = [out3["c_status_desc_chn"]for out3 in outs3]
                shidlist = [out3["c_status_code"]for out3 in outs3]
                
            # 查询收藏家  'c_status_code': 收藏家184 鑒賞家143 藏書家144
            jcj=0
            if any(elem in [184,143,144] for elem in shidlist):
                jcj=1
            # 查询文人 165文人 9书法家 71畫家 114诗人 210小说家 235词人
            wr=0
            if any(elem in [9,71,114,165,210,235] for elem in shidlist):
                wr=1
            hj = False
            # 社会分区有画家或者整理的画家列表中有这人，判断为画家
            if 71 in shidlist or out["c_name_chn"] in self.painterlist:
                hj=True
                # wr=1
            # if out["c_name_chn"]=="黃公望":print(shlist,shidlist)
            # 查询任官级别
            sql = "select c_personid,c_office_chn \
                    from POSTED_TO_OFFICE_DATA ,OFFICE_CODES \
                    where POSTED_TO_OFFICE_DATA.c_office_id = OFFICE_CODES.c_office_id\
                    and c_personid = {}".format(cid)
            outs5= select(self.dbpath,sql)
            highest_office=0
            for out5 in outs5:
                office_chn=cc.convert(out5["c_office_chn"])
                if office_chn in gzpj:
                    highest_office=max(highest_office,gzpj[office_chn]["得分"])
            # 皇帝单独处理,皇帝的社会分区是26,但是这个分区不全面
            if 26 in shidlist:
                highest_office=20
            if out["c_name_chn"] in ["愛新覺羅弘曆","愛新覺羅顒琰","(愛新覺羅)溥儀"]:
                highest_office=20
            # 特殊处理区域
            if out["c_name_chn"]=="納蘭性德":
                highest_office=12
                jcj=1
            if out["c_name_chn"]=="詹景鳳":
                out["c_birthyear"]=1532
                out["c_deathyear"]=1602
            if out["c_name_chn"]=="黃公望":
                wr=1
                shlist="畫家"
            info={
                "姓名":out["c_name_chn"],
                "生年":out["c_birthyear"],
                "卒年":out["c_deathyear"],
                "别名":bmlist,
                "籍贯":jg,
                "朝代":dynasty,
                "社会区分":shlist,
                "画家":hj,
                "身份(鉴藏家、文人、官员)":[jcj,wr,highest_office]
            }
            tmpid2info[cid]=info
        return tmpid2info
    
    def select_kin(self,cidlist):
        # 获取人物列表之间的亲缘关系
        sql = "select kin_data.c_personid,c_kin_id,c_kinrel_chn from kin_data,kinship_codes\
            where kin_data.c_kin_code=kinship_codes.c_kincode\
            and kin_data.c_personid in {} and kin_data.c_kin_id in {}".format(
            tuple(cidlist) if len(cidlist) > 1 else "({})".format(cidlist[0]),
            tuple(cidlist) if len(cidlist) > 1 else "({})".format(cidlist[0]))
        outs = select(self.dbpath,sql)
        kinlist=[{"人1id":out["c_personid"],"人2id":out["c_kin_id"],
               "关系":out["c_kinrel_chn"],"关系类型":"亲缘",
               "起始年":None,"结束年":None,"地点":None}for out in outs]
        # print(kinlist)
        return kinlist
    
    def select_assoc(self,cidlist):
        # 获取人物列表之间的社会关系
        sql = "select c_assoc_code,c_personid,c_assoc_id,c_assoc_year,c_addr_id from assoc_data\
                where c_personid in {} and c_assoc_id in {}".format(
                tuple(cidlist) if len(cidlist) > 1 else "({})".format(cidlist[0]),
                tuple(cidlist) if len(cidlist) > 1 else "({})".format(cidlist[0]))
        outs = select(self.dbpath,sql)
        assoclist=[]
        for out in outs:
            # 处理没有记录的时间地点
            if out["c_assoc_year"]in[None,0,-1]:out["c_assoc_year"]=None
            if out["c_addr_id"]in[None,0,-1]:addr=None
            else:
                #查询地点
                sql = "select c_name_chn from addr_codes where c_addr_id={}".format(out["c_addr_id"])
                addr = select(self.dbpath,sql)[0]["c_name_chn"]
            if str(out["c_assoc_code"]) in self.id2rela:
                gxms = self.id2rela[str(out["c_assoc_code"])]["关系描述"]
                gxlx = self.id2rela[str(out["c_assoc_code"])]["关系类型"]
            else:
                gxms = "未知"
                gxlx = "其他"
            assoc = {"人1id":out["c_personid"],"人2id":out["c_assoc_id"],
                    "关系":gxms,
                    "关系类型":gxlx,
                    "起始年":out["c_assoc_year"],"结束年":None,"地点":addr}
            assoclist.append(assoc)
        # print(assoclist)
        return assoclist

    def select_office(self,cidlist):
        # 任官事件作为和自己的政治关系
        sql = "select c_personid,c_office_id,c_posting_id,c_firstyear,c_lastyear\
                from POSTED_TO_OFFICE_DATA \
                where c_personid in {}".format(
                tuple(cidlist) if len(cidlist) > 1 else "({})".format(cidlist[0]))
        outs = select(self.dbpath,sql)
        officelist=[]
        # print(outs)
        for out in outs:
            #查一下地名
            sql = "select c_name_chn from POSTED_TO_ADDR_DATA,addr_codes\
                where POSTED_TO_ADDR_DATA.c_addr_id=addr_codes.c_addr_id\
                and c_posting_id = {}".format(out["c_posting_id"])
            out1 = select(self.dbpath,sql)
            addr = None
            if out1: addr=out1[0]["c_name_chn"]
            if addr=="[未詳]":addr=None
            # 查一下官职名
            sql = "select c_office_chn from office_codes\
                where c_office_id = {}".format(out["c_office_id"])
            out2 = select(self.dbpath,sql)
            officename= None
            if out2: officename = out2[0]["c_office_chn"]
            office={"人1id":out["c_personid"],"人2id":out["c_personid"],
                    "关系":"任职"+officename,"关系类型":"政治",
                    "起始年":out["c_firstyear"],"结束年":out["c_lastyear"],"地点":addr}
            officelist.append(office)
        return officelist

    def select_one_person(self,cid):
        # 获取某人的关系网
        cidlist=[cid]# 人物列表加入主角
        # 获取一度亲属
        sql="select c_kin_id from kin_data where c_personid={}".format(cid)
        outs = select(self.dbpath,sql)
        for out in outs: cidlist.append(out["c_kin_id"])
        # 获取一度关系者
        sql="select c_assoc_id from assoc_data where c_personid={}".format(cid)
        outs = select(self.dbpath,sql)
        for out in outs: cidlist.append(out["c_assoc_id"])
        cidlist=list(set(cidlist))
        # 获取人物列表信息
        tmpid2info = self.getid2info(cidlist)
        # 获取列表人物之间关系
        kinlist = self.select_kin(cidlist)
        assoclist = self.select_assoc(cidlist)
        officelist = self.select_office(cidlist)
        kinlist.extend(assoclist)
        kinlist.extend(officelist)
        # 关系排序
        def cmp(s1, s2):
            res1=0
            res2=0
            if s1["人1id"]==int(cid) or s1["人2id"]==int(cid):res1 += 10
            if s2["人1id"]==int(cid) or s2["人2id"]==int(cid):res2+=10
            if s1["地点"]!=None : res1 += 1
            if s2["地点"]!=None : res2 += 1
            return res2-res1

        kinlist =sorted(kinlist,key=cmp_to_key(cmp))
        # print(len(kinlist))
        result = {
            "关系列表":kinlist,
            "人物信息":tmpid2info
        }
        return result

    def count_rela(self,cidlist):
        # 结果列表
        personinfos={cid:{"分数":{"古籍讨论":0,"画派":0},
                        "相关画作":{},"相关社交":{},"相关文学":{},
                        "相关政治":{},"相关亲缘":{},"相关其他":{},
                        "全部关系数量":{"画作":0,"社交":0,"文学":0,"政治":0,"亲缘":0,"其他":0},
                        "全部关系年份":{"画作":{},"社交":{},"文学":{},"政治":{},"亲缘":{},"其他":{}}}
                     for cid in cidlist}
        gjdf=pd.read_excel("data/古籍讨论度new.xlsx")
        with open("data/画派信息.json","r",encoding="UTF8")as f:
            hpinfo=json.load(f)
        #个人生卒年
        id2info = self.getid2info(cidlist)
        for cid in id2info:
            personinfos[cid]["姓名"]=id2info[cid]["姓名"]
            personinfos[cid]["生年"]=id2info[cid]["生年"]
            personinfos[cid]["卒年"]=id2info[cid]["卒年"]
            personinfos[cid]["分数"]["鉴藏家"]=id2info[cid]["身份(鉴藏家、文人、官员)"][0]
            personinfos[cid]["分数"]["文人"]=id2info[cid]["身份(鉴藏家、文人、官员)"][1]
            personinfos[cid]["分数"]["最高官职"]=id2info[cid]["身份(鉴藏家、文人、官员)"][2]
            if gjdf[gjdf["题跋人"]==id2info[cid]["姓名"]]["古籍出现次数"].any():
                personinfos[cid]["分数"]["古籍讨论"]=int(
                    gjdf[gjdf["题跋人"]==id2info[cid]["姓名"]]["古籍出现次数"].values[0])
            # else: print(id2info[cid]["姓名"])
            if id2info[cid]["姓名"] in hpinfo:
                personinfos[cid]["分数"]["画派得分"]=hpinfo[id2info[cid]["姓名"]]
            
        # 统计人物在列表之间的的六种关系
        kinlist = self.select_kin(cidlist)
        assoclist = self.select_assoc(cidlist)
        officelist = self.select_office(cidlist)
        kinlist.extend(assoclist)
        kinlist.extend(officelist)
        
        for rela in kinlist:
            if rela["人1id"]==rela["人2id"]:continue # 和自己的关系无需连线
            if rela["人2id"] not in personinfos[rela["人1id"]]["相关"+rela["关系类型"]]:
                personinfos[rela["人1id"]]["相关"+rela["关系类型"]][rela["人2id"]]=[rela]
            else:
                personinfos[rela["人1id"]]["相关"+rela["关系类型"]][rela["人2id"]].append(rela)
        
        # 每个人物的全部关系,只统计年份
        for cid in cidlist:
            # 亲缘，无年份
            sql = "select * from kin_data where c_personid={}".format(cid)
            outs = select(self.dbpath,sql)
            personinfos[cid]["全部关系数量"]["亲缘"]+=len(outs)
            # 任官关系
            sql ="select c_firstyear from POSTED_TO_OFFICE_DATA \
                where c_personid={}".format(cid)
            outs = select(self.dbpath,sql)
            for out in outs:
                personinfos[cid]["全部关系数量"]["政治"]+=1
                if out["c_firstyear"]in[None,0,-1]:continue # 没有时间的不用记录时间
                if out["c_firstyear"] in personinfos[cid]["全部关系年份"]["政治"]:
                    personinfos[cid]["全部关系年份"]["政治"][out["c_firstyear"]]+=1
                else:
                    personinfos[cid]["全部关系年份"]["政治"][out["c_firstyear"]]=1
            # 标准关系
            sql = "select c_assoc_code,c_assoc_year from assoc_data \
                where c_personid={}".format(cid)
            outs = select(self.dbpath,sql)
            for out in outs:
                relatype = self.id2rela[str(out["c_assoc_code"])]["关系类型"]
                personinfos[cid]["全部关系数量"][relatype]+=1
                if out["c_assoc_year"]in[None,0,-1]:continue# 没有时间的不用记录时间
                if out["c_assoc_year"] in personinfos[cid]["全部关系年份"][relatype]:
                    personinfos[cid]["全部关系年份"][relatype][out["c_assoc_year"]]+=1
                else:
                    personinfos[cid]["全部关系年份"][relatype][out["c_assoc_year"]]=1


        return personinfos


reladto=RelaDto()

if __name__ == '__main__':
    cidlist=[17690,10183,17689]
    # print(select_kin(cidlist))
    reladto.save_id2info(reladto.getid2info(cidlist))
    cidlist = [cid for cid in reladto.id2info]
    # print(reladto.id2info)
    # reladto.select_kin(cidlist)
    # reladto.select_assoc(cidlist)
    reladto.id2info.update(reladto.getid2info([17690,10815]))
    print(reladto.id2info)
    # print(reladto.select_one_person(17690))

