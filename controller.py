from flask import Flask,url_for, redirect,request
from flask_cors import CORS, cross_origin
import json
import os

from server import *
from RestData import R
# from ner.getresulthc import infer,JsonEncoder
# from ner.dealsent import getsentences,predealh
# from ner.findperson import searchfen

app = Flask("ghzj_backend")
app.config['JSON_AS_ASCII'] = False
CORS(app)
 
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

@app.route('/getciyun/<pid>', methods=['GET'])
@cross_origin(allow_headers="*")
def getciyun(pid):
    # 词云数据
    resultnerfile = "nerresult/"+pid+".json"
    if os.path.exists(resultnerfile):
        result = ciyun(pid)
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

@app.route("/getAssocData/<name>", methods=['GET'])
@cross_origin(allow_headers="*")
# @cross_origin(allow_headers="*")
def getAssocData(name):
    result = assocdata(name)
    return R.ok(result)

@app.route("/getauinfoscore/<pid>", methods=['GET'])
@cross_origin(allow_headers="*")
def getauinfoscore(pid):
    # 作者生卒年和得分
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

@app.route("/getauthorlist/<pid>", methods=['GET'])
@cross_origin(allow_headers="*")
def getauthorlist(pid):
    # 印章题跋作者列表
    resultnerfile = "nerresult/"+pid+".json"
    if os.path.exists(resultnerfile):
        result = authorlist(pid)
        return R.ok(result)
    return R.erro2()

@app.route("/getpainting/<pid>",methods=['GET'])
@cross_origin(allow_headers="*")
def getpainting(pid):
    # 获取画作图像
    result = painting(pid)
    return R.ok(result)

@app.route("/getcoor",methods=['GET',"POST"])
@cross_origin(allow_headers="*")
def getcoor():
    x=int(request.args.get("x"))
    y=int(request.args.get("y"))
    if (x in range(0,9000)) and (y in range(0,1000)):
        result = coor(x,y)
        return R.ok(result)
    return R.erro2()

 
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=28081, debug = True)