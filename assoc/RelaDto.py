from tool import select
import json
class RelaDto():
    # 该类用于查询人物信息以及人物关系
    def __init__(self,path="data/latest.db"):
        self.dbpath = path
        self.id2info ={}
        # 已经查询到信息的人物列表，长期存储
        with open("data/id2info.json","r",encoding="UTF8")as f:
            self.id2info = json.load(f) 
        self.tmplist_matrix = {} # 临时人物列表
        self.tmplist_socre = {}
        self.tmppid_matrix = -1 # 临时记录画作id
        self.tmppid_score = -1
        # 关系id转关系名和类别
        with open ("data/id2rela.json","r",encoding="UTF8")as f:
            self.id2rela = json.load(f)

    def save_id2info(self,tmpid2info):
        # 存储新的人物信息
        self.id2info.update(tmpid2info)
        with open("data/id2info.json","w",encoding="UTF8")as f:
            json.dump(self.id2info,f,indent=2, ensure_ascii=False)

    def getid2info(self,cidlist):
        # 获取人物列表的cid-信息对
        tmpid2info={}
        for cid in cidlist:
            # 如果已经存储了人物信息就直接调用
            if cid in self.id2info:
                tmpid2info[cid]=self.id2info[cid]
                cidlist.remove(cid)

        sql = "select c_personid,c_name_chn,c_birthyear,c_deathyear,c_index_addr_id\
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
            # 社会区分
            sql = "select c_status_desc_chn from status_data,status_codes\
                    where status_data.c_status_code=status_codes.c_status_code\
                    and c_personid = {}".format(cid)
            outs3 = select(self.dbpath,sql)
            shlist=None # 避免没有社会区分报错
            if outs3: shlist = [out3["c_status_desc_chn"]for out3 in outs3]

            info={
                "姓名":out["c_name_chn"],
                "生年":out["c_birthyear"],
                "卒年":out["c_deathyear"],
                "别名":bmlist,
                "籍贯":jg,
                "社会区分":shlist
            }
            tmpid2info[cid]=info
        self.save_id2info(tmpid2info)#存储新增的id2info，下次不用再查
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
            assoc = {"人1id":out["c_personid"],"人2id":out["c_assoc_id"],
                    "关系":self.id2rela[str(out["c_assoc_code"])]["关系描述"],
                    "关系类型":self.id2rela[str(out["c_assoc_code"])]["关系类型"],
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
        # print(len(kinlist))
        result = {
            "关系列表":kinlist,
            "人物信息":tmpid2info
        }
        return result

    def count_rela(self,cidlist):
        # 结果列表
        personinfos={cid:{"相关画作":{},"相关社交":{},"相关文学":{},
                          "相关政治":{},"相关亲缘":{},"相关其他":{},
                          "全部关系数量":{"画作":0,"社交":0,"文学":0,"政治":0,"亲缘":0,"其他":0},
                          "全部关系年份":{"画作":{},"社交":{},"文学":{},"政治":{},"亲缘":{},"其他":{}}}
                     for cid in cidlist}
        #个人生卒年
        id2info = self.getid2info(cidlist)
        for cid in id2info:
            personinfos[cid]["生年"]=id2info[cid]["生年"]
            personinfos[cid]["卒年"]=id2info[cid]["卒年"]
        # 查询收藏家  'c_status_code': 收藏家184 鑒賞家143 藏書家144
        sql = "select c_personid from status_data where c_status_code in (184,143,144) \
                and c_personid in {}".format(
                tuple(cidlist) if len(cidlist) > 1 else "({})".format(cidlist[0]))
        outs= select(self.dbpath,sql)
        # print(len(outs))
        if outs:
            for out in outs:
                personinfos[out["c_personid"]]["鉴藏家"]=1
        # 查询任官
        
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
            for out in outs:
                personinfos[cid]["全部关系数量"]["亲缘"]+=1
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
                if out["c_assoc_year"] in personinfos[cid]["全部关系年份"]["政治"]:
                    personinfos[cid]["全部关系年份"]["政治"][out["c_assoc_year"]]+=1
                else:
                    personinfos[cid]["全部关系年份"]["政治"][out["c_assoc_year"]]=1


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

