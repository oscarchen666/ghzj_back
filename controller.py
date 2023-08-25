from flask import Flask,url_for, redirect,request
from flask_cors import CORS, cross_origin
import json
import os

from server import *
from RestData import R
from tool import makecname2id
# from ner.getresulthc import infer,JsonEncoder
# from ner.dealsent import getsentences,predealh
# from ner.findperson import searchfen

app = Flask("ghzj_backend")
app.config['JSON_AS_ASCII'] = False
CORS(app)
# metrics = PrometheusMetrics(app) 
 
@app.route('/')
@cross_origin(allow_headers="*")
def hello():
    return "<p>Hello, World!</p>"

@app.route('/resultner/<pid>', methods=['GET'])
@cross_origin(allow_headers="*")
def resultner(pid):
    # 根据画作id直接取生成好的ner结果
    # pid = request.args.get("pid")
    resultnerfile = "nerresult/"+pid+".json"
    if os.path.exists(resultnerfile):
        with open(resultnerfile,"r",encoding="UTF8")as f:
            data = json.load(f)
        return R.ok(data["sentences"])
    
    return redirect(url_for('newner',pid=pid))

@app.route('/newner/<pid>', methods=['GET'])
@cross_origin(allow_headers="*")
def newner(pid):
    # 根据画作id生成ner结果
    # pid = request.args.get("pid")
    origfile = "orig/"+pid+".json"
    if os.path.exists(origfile):
        data = ner_search(pid)
        return R.ok(data["sentences"])
    return R.erro2()

@app.route('/getpaintinglist', methods=['GET'])
@cross_origin(allow_headers="*")
def getpaintinglist():
    # 获取全部画作列表（画作名+pid）
    plist = paintinglist()
    return R.ok(plist)

@app.route('/getciyun/<pid>', methods=['GET'])
@cross_origin(allow_headers="*")
def getciyun(pid):
    # 词云数据
    resultnerfile = "nerresult/"+pid+".json"
    if os.path.exists(resultnerfile):
        result = ciyun(pid)
        return R.ok(result)
    return R.erro2()

@app.route("/getauthorlist/<pid>", methods=['GET'])
@cross_origin(allow_headers="*")
def getauthorlist(pid):
    # 印章题跋作者列表
    resultnerfile = "nerresult/"+pid+".json"
    if os.path.exists(resultnerfile):
        result = authorlist(pid)
        return R.ok(result)
    return R.erro2()

@app.route('/getlines/<pid>/<name>', methods=['GET'])
@cross_origin(allow_headers="*")
def getlines(pid,name):
    #作者和词云、图像连线数据
    resultnerfile = "nerresult/"+pid+".json"
    if os.path.exists(resultnerfile):
        result = lianxian(pid,name)
        return R.ok(result)
    return R.erro2()

@app.route('/getgaoliang/<pid>/<name>/<type>', methods=['GET','POST'])
@cross_origin(allow_headers="*")
def getgaoliang(pid,name,type):
    # 词云和题跋之间高亮关联
    resultnerfile = "nerresult/"+pid+".json"
    if os.path.exists(resultnerfile):
        result = gaoliang(pid,name,type)
        return R.ok(result)
    return R.erro2()

@app.route("/getauinfoscore/<pid>", methods=['GET'])
@cross_origin(allow_headers="*")
def getauinfoscore(pid):
    # 作者生卒年和得分
    # 废弃
    resultnerfile = "authorinfo/"+pid+".json"
    if os.path.exists(resultnerfile):
        result = auinfoscore(pid)
        return R.ok(result)
    return R.erro2()

@app.route("/getyinzhanglist/<pid>", methods=['GET'])
@cross_origin(allow_headers="*")
def getyinzhanglist(pid):
    # 印章列表
    result = yinzhang(pid)
    return R.ok(result)

@app.route("/changeyinzhang", methods=['GET'])
@cross_origin(allow_headers="*")
def changeyinzhang():
    # 更改印章匹配结果
    pid = request.args.get("pid")
    yinzhang_imgs = request.args.get("yzids").split(",")
    ppids = request.args.get("ppids").split(",")
    if len(yinzhang_imgs)==len(ppids) and os.path.exists(f"nerresult/{pid}.json"):
        result = changeyz(pid, yinzhang_imgs, ppids)
        return R.ok(result)
    return R.erro2()

@app.route("/getimg",methods=['GET',"POST"])
@cross_origin(allow_headers="*")
def getimg():
    imgid = request.args.get("imgid")
    imgtype = request.args.get("imgtype")
    if imgtype in ["截图","匹配","画作","画心","新图"]:
        result = image(imgid,imgtype)
        return R.ok(result)
    return R.erro2()

@app.route("/getcoor",methods=['GET',"POST"])
@cross_origin(allow_headers="*")
def getcoor():
    x=int(request.args.get("x"))
    y=int(request.args.get("y"))
    if (x in range(0,9000)) and (y in range(0,1000)):
        result = coor(x,y)
        return R.ok(result)
    return R.erro2()

@app.route("/gethuaxin/<pid>",methods=['GET'])
@cross_origin(allow_headers="*")
def gethuaxin(pid):
    result=huaxininfo(pid)
    return R.ok(result)

@app.route("/getpersonnet", methods=['GET'])
@cross_origin(allow_headers="*")
def getpersonnet():
    # 查询和该人物相关的关系图谱
    cid = int(request.args.get("cid"))
    result = personnet(cid)
    return R.ok(result)

@app.route("/getpersonmatrix",methods=['GET'])
@cross_origin(allow_headers="*")
def getpersonmatrix():
    # 查询人物列表之间的关系以及人物信息
    pid=request.args.get("pid")
    addnames=request.args.get("addnames").split(",")
    addcids=request.args.get("addcids").split(",")
    
    if os.path.exists("nerresult/"+pid+".json") and not os.path.exists("authorinfo/"+pid+".json"):
        # 没生成作者列表，现场生成
        authorlist(pid)    
    if os.path.exists("authorinfo/"+pid+".json") and len(addnames)==len(addcids):
        # 得有作者列表并且参数长度一致
        cname2id = makecname2id(addnames,addcids)# 新增人物列表预处理
        result=personmatrix(pid,cname2id)
        return R.ok(result)
    return R.erro2()

@app.route("/getpersonscore", methods=["GET"])
@cross_origin(allow_headers="*")
def getpersonscore():
    # 查询人物关系计算得分
    pid=request.args.get("pid")
    addnames=request.args.get("addnames").split(",")
    addcids=request.args.get("addcids").split(",")
    
    if os.path.exists("nerresult/"+pid+".json") and not os.path.exists("authorinfo/"+pid+".json"):
        # 没生成作者列表，现场生成
        authorlist(pid)  
    if os.path.exists("authorinfo/"+pid+".json") and len(addnames)==len(addcids):
        # 得有作者列表并且参数长度一致
        cname2id = makecname2id(addnames,addcids)# 新增人物列表预处理
        result=personscore(pid,cname2id)
        return R.ok(result)
    return R.erro2(msg ="请先请求/getauthorlist/")

@app.route("/getonestringinfo", methods=["GET"])
@cross_origin(allow_headers="*")
def getonestringinfo():
    # 用名字查询可能的人物
    name=request.args.get("name")
    stype=request.args.get("stype")
    if len(name)>1 and stype in["cperson","aperson","cplace","aplace","time"]:
        result = onestringinfo(name,stype)
        return R.ok(result)
    return R.erro2()

@app.route("/getcid2name", methods=["GET"])
@cross_origin(allow_headers="*")
def getcid2name():
    # cid查询人名
    cid=request.args.get("cid")
    result = cid2name(cid)
    if result:
        return R.ok(result)
    return R.erro2()

 
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=28081, debug = True)    