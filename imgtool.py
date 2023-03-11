import os

def return_img_stream(img_local_path):
    """
    工具函数:
    获取本地图片流
    :param img_local_path:文件单张图片的本地绝对路径
    :return: 图片流
    """
    import base64
    img_stream = ''
    with open(img_local_path, 'rb') as img_f:
        img_stream = img_f.read()
        img_stream = base64.b64encode(img_stream).decode()
    return img_stream

def imgexists(fullpath):
    # 图片找不到时用空白图替代
    if os.path.exists(fullpath):
        return return_img_stream(fullpath)
    
    # return "这里是图片"
    return return_img_stream("data/暂缺.png")

