from flask import jsonify

class copy_utils:
    
    @staticmethod
    def obj_to_dic(obj):
        '''
        将传入的data对象转成字典
        '''
        result = {}
        for temp in obj.__dict__:
            if temp.startswith('_') or temp == 'metadata':
                continue
            result[temp] = getattr(obj, temp)
        return result
    
    @staticmethod
    def obj_to_list(list_obj):
        '''
        将传入的data对象转成List,list中的元素是字典
        '''
        result = []
        for obj in list_obj:
            result.append(copy_utils.obj_to_dic(obj))
        return result
        
class R(object):
    
    @staticmethod
    def ok(data):
        result = {"code":"200","msg":"操作成功","data":data}
        return jsonify(result)
    
    @staticmethod
    def erro1(code = 500,msg = "系统异常"):
        result = {"code":code,"msg":msg}
        return jsonify(result)
    
    @staticmethod
    def erro2(code = 511,msg = "参数有误或缺少对应文件"):
        result = {"code":code,"msg":msg}
        return jsonify(result)
