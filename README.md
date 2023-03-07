# ghzj_back
国画传记后端

经验不足，框架比较乱，见谅

建议使用conda环境
```
conda create -n ghzj_back python==3.7
conda activate ghzj_back
pip install -r requirements.txt
```
需要下载cbdb数据库"last.db"放在主目录
运行：
```python controller.py```

文件框架：
controller.py:接口、项目启动文件
server.py:主要业务逻辑
RestData.py:返回数据类
其他py文件:比较复杂的模型、数据处理

