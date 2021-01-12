# -*- coding: utf-8 -*-
import re
import sys
import logging
import threading

from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import connections
from django.conf import settings

from .config import API_TABLE_MAPPING

'''
settings.py 文件可以设置的配置项
SIMPLE_CRUD_DB
SIMPLE_CRUD_MAPPING
SIMPLE_CRUD_DANGER_STR
SIMPLE_CRUD_LOGGER
SIMPLE_CRUD_BASEVIEW

'''
API_TABLE_MAPPING = getattr(settings, 'SIMPLE_CRUD_MAPPING', API_TABLE_MAPPING)

BASEVIEW = getattr(settings, 'SIMPLE_CRUD_BASEVIEW', APIView)

DEFAULT_DB=getattr(settings, 'SIMPLE_CRUD_DB', 'default')

DEFAULT_DANGER_STR=getattr(settings, 'SIMPLE_CRUD_DANGER_STR', ';|"|@|`|\'|\\\\')

logger_name=getattr(settings,'LOGGING',{}).get('SIMPLE_CRUD_LOGGER')


def simple_logger(name,stream=sys.stdout,level=logging.DEBUG,format="%(asctime)s - %(message)s"):
    """获取简易的日志对象 只是线程安全"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    format = logging.Formatter(format)                      # output format 
    sh = logging.StreamHandler(stream=stream)               
    sh.setFormatter(format)
    logger.addHandler(sh)
    
    return logger


if logger_name:
    logger=logging.getLogger(logger_name)
else:
    logger=simple_logger('test')
    
#class logger():
#    pass
#
#logger.debug=logger.error=logger.info=print


def get_opt_limits_sub_by_keys(keys,opt_limits,limit_offset=0,match_type='>='):
    """
    由字段名过滤，获取匹配的字段限制条件
    """
    opt_limits_sub=[]
    danger_check=''
    if not opt_limits:
        return opt_limits,danger_check
    
    for l in opt_limits:
        _keys=l[limit_offset].keys()
        
        if match_type=='>=':
            #只需要确保传入的条件大于配置的条件，之后的操作再做值判断 where条件使用
            if set(keys)>=set(_keys) or not _keys:
                opt_limits_sub.append(l)
         
        elif match_type=='==':
            #只需要确保传入的条件恒等于配置的条件      insert update的值判断时使用
            if set(keys)==set(_keys) or not _keys:
                opt_limits_sub.append(l)   
        
        elif match_type=='<=':
            #只需要确保传入的条件小于配置的条件，之后的操作再做值判断
            if set(keys)<=set(_keys) or not _keys:
                opt_limits_sub.append(l)
    
    if not opt_limits_sub:
        danger_check='columns number not enough'
    return opt_limits_sub,danger_check


def get_opt_limits_sub_by_kv(key,value,opt_limits,limit_offset=0,transfer_value=1):
    """
    由字段以及字段值，获取匹配的字段限制条件
    """
    opt_limits_sub=[]
    danger_check=''
    if not opt_limits:
        return opt_limits,danger_check
    
    if transfer_value:
        try:
            value=int(value)
        except:
            pass
    
    for l in opt_limits:
        if not key in l[limit_offset]:
            '''
            #允许额外的传入条件 但额外的传入条件只能为等值 且不能出现 or
            if key[0] != '|' and not key[-1] in ['!','>','<']:
            '''
            #允许额外的传入条件 但额外的传入条件不能出现 or
            if key[0] != '|':
                opt_limits_sub.append(l)
        else: 
            v_limit=l[limit_offset][key]
            if not v_limit:
                # 为空则允许任意传入的条件
                opt_limits_sub.append(l)
            else:
                if (isinstance(v_limit,str) or isinstance(v_limit,int)) and v_limit==value:
                    #str/int  等值过滤
                    opt_limits_sub.append(l)
                #elif isinstance(v_limit,str)  and isinstance(value,str) and re.match(v_limit,value):
                elif isinstance(v_limit,str) and re.match(v_limit,str(value)):
                    #正则过滤
                    opt_limits_sub.append(l)
                elif isinstance(v_limit,list) and isinstance(value,int) and value>=v_limit[0] and (len(v_limit)==1 or value<=v_limit[1]):
                    #[] 范围过滤
                    opt_limits_sub.append(l)
                elif isinstance(v_limit,set) and value in v_limit:
                    #{} 枚举过滤
                    opt_limits_sub.append(l)
                    
    if not opt_limits_sub:
        danger_check='key value not match' 
    
    return opt_limits_sub,danger_check


def get_opt_limits_sub_select(select_columns,opt_limits,limit_offset=1):
    """
    select的选择字段，获取匹配的字段限制条件
    select_columns='*'
    select_columns='a,b,c'
    """
    opt_limits_sub=[]
    danger_check=''
    if not opt_limits:
        return opt_limits,danger_check
    
    for l in opt_limits:
        _select_columns=l[limit_offset]
        if not _select_columns:
            #为空 表明所有字段都允许查询
            opt_limits_sub.append(l)
        elif set(select_columns.split(','))<=set(_select_columns):
            opt_limits_sub.append(l)
    
    if not opt_limits_sub:
        danger_check='select columns out of limit'    
    return opt_limits_sub,danger_check
    

def transfer_field(field,or_conn=' OR ',and_conn=' AND '):
    """
    由url的key转换成sql的字段
    """
    break_flag=''
    _k=field
    ao_pre=''
    connector=and_conn
    if field[0]=='|':
        _k=field[1:]
        connector=or_conn
        
    if field[-1] == '%':
        if len(field)>=2 and field[-2] == '!':
            _k=_k[:-2]
            ao_pre=field[-2:]
        else:
            _k=_k[:-1]
            ao_pre=field[-1]
    
    elif field[-1] in ['!','>','<']:
        _k=_k[:-1]
        ao_pre=field[-1]
    return break_flag,connector,_k,ao_pre


def transfer_value(value,ao_pre,default_ao='='):
    """
    转换url的value
    """
    break_flag=''
    v=value
    v_format='%s'
    if ao_pre == '%':
        _ao=' LIKE '
    elif ao_pre == '!%':
        _ao=' NOT LIKE '
    else:
        _ao=ao_pre+default_ao
        try:
            v=int(value)
        except ValueError: 
            if v.lower()=='null':
                v_format='null'
                v=''
                if not ao_pre:
                    _ao=' IS '
                elif ao_pre=='!':
                    _ao=' IS NOT '
                else:
                    break_flag='only is / is not allow for null condition_format'
    
    return break_flag, _ao, v, v_format


def params2condition(params,opt,opt_limits,danger_str=DEFAULT_DANGER_STR):
    """
    params url字典类型参数 
    {'a':'aaa','b':'bbb'}  => 'WHERE a=%s and b=%s' ['aaa','bbb']
    """
    danger_check=''
    select_columns='*'
    condition_format=''
    condition_args=[]
    opt_limits_sub=opt_limits                #匹配的子条件 可能下一层条件过滤需要
    limit_sub=''                             
    
    and_conn=' AND '
    or_conn=' OR '
    limit_conn=' LIMIT '
    where_conn='WHERE '
    default_ao='='   #Arithmetic Operators
    
    #先确保字段数匹配
    logger.debug("origin where keys limits: %s %s" % (list(params.keys()), opt_limits_sub))
    opt_limits_sub,danger_check=get_opt_limits_sub_by_keys(params.keys(),opt_limits_sub)
    logger.debug("where keys limits: %s %s" % (list(params.keys()), opt_limits_sub))
    for k in params:
        if danger_check:
            break
        _k=k
        if k=='_' :
            if opt == 'select' and params[k]:
                for c in params[k]:
                    if danger_str and re.search(danger_str,c):
                        danger_check='should be normal in column name'
                
                if not danger_check:      
                    select_columns='`'+params[k].replace(',','`,`')+'`'
                    logger.debug("origin select columns limits: %s %s" % (params[k],str(opt_limits_sub)))
                    opt_limits_sub,danger_check=get_opt_limits_sub_select(params[k],opt_limits_sub)
                    logger.debug("select columns limits: %s %s" % (params[k],str(opt_limits_sub)))
                    
        elif k=='__' :   
            if opt == 'select' and params[k]:
                limit_sub = limit_conn+params[k]
                _limit = params[k].split(',')
                #print(_limit)
                if len(_limit)!=1 and len(_limit)!=2:
                    limit_sub=''
                    danger_check='limit length not match'
                for l in _limit:
                    try:
                        int(l)
                    except:
                        limit_sub=''
                        danger_check='should be int in limit'
                        break
        
        elif danger_str and re.search(danger_str,k):
            danger_check='should be normal in column name'
        else:
            #逐字段过滤
            logger.debug("origin where kv limits: %s %s %s" % (k, params[k],str(opt_limits_sub)))
            opt_limits_sub,danger_check=get_opt_limits_sub_by_kv(k, params[k], opt_limits_sub)
            logger.debug("where kv limits: %s %s %s" % (k, params[k],str(opt_limits_sub)))
            if danger_check:
                break
            
            break_flag, connector,_k,ao_pre=transfer_field(k)
            if break_flag:
                danger_check=break_flag
                break
            
            break_flag, _ao, v, v_format = transfer_value(params[k],ao_pre)
            if break_flag:
                danger_check=break_flag
                break            
            
            if v or int(v)==0:
                condition_args.append(v)
                
            condition_format += connector+('`%s`%s%s' % (_k, _ao, v_format))
            
    if re.match(and_conn,condition_format):
        condition_format=condition_format[len(and_conn):]  
    elif re.match(or_conn,condition_format):
        condition_format=condition_format[len(or_conn):]  
    
    if condition_format:
        condition_format=where_conn+condition_format
    
    if opt=='select':
        if not limit_sub:
            #select 默认分页
            limit_sub=' LIMIT 10'
            
        if not danger_check and select_columns=='*':
            logger.debug("origin select columns limits: %s %s" % (select_columns,str(opt_limits_sub)))
            opt_limits_sub,danger_check=get_opt_limits_sub_select(select_columns,opt_limits_sub)
            logger.debug("select columns limits: %s %s" % (select_columns,str(opt_limits_sub)))
    
        condition_format += limit_sub
    
    return danger_check, condition_format, condition_args, select_columns,opt_limits_sub

    
def dict2insetinfo(data,opt_limits,danger_str=DEFAULT_DANGER_STR):
    """
    post提交的信息转换成insert语句的片段
    [{a:aaa,b:bbb}]  =>  [["a,b",["aaa","bbb"]]]
    
    "insert into ttt(a,b) values(%s,%s);"
    """
    danger_check=''
    insetinfo=[]
    opt_limits_sub=opt_limits
    for d in data:
        if danger_check:
            break
    
        _column="" 
        _data=[]
        __data=[]
        
        #插入的字段必须恒等于配置的字段
        logger.debug("origin insert keys limits: %s %s" % (list(d.keys()),str(opt_limits_sub)))
        opt_limits_sub,danger_check=get_opt_limits_sub_by_keys(d.keys(),opt_limits_sub,limit_offset=1,match_type='==')  
        logger.debug("insert keys limits: %s %s" % (list(d.keys()),str(opt_limits_sub)))
        if danger_check:
            break
        
        for k in d:
            if danger_str and re.search(danger_str,k):
                danger_check='should be normal in column name'
                data=[]
                break
            
            #逐个插入值判断
            logger.debug("origin insert kv limits: %s %s %s" % (k,d[k],str(opt_limits_sub)))
            opt_limits_sub,danger_check=get_opt_limits_sub_by_kv(k,d[k],opt_limits_sub,limit_offset=1,transfer_value=0)
            logger.debug("insert kv limits: %s %s %s" % (k,d[k],str(opt_limits_sub)))
            if danger_check:
                break
             
            _column += ',`'+k+'`'
            _data.append(d[k])
        _column=_column[1:]
        _column_format=(',%s'*len(_data))[1:]
        insetinfo.append([_column,_column_format,_data])
    
    return danger_check,insetinfo
    

def dict2updateinfo(data,opt_limits,danger_str=DEFAULT_DANGER_STR):   
    """ 
    post提交的信息转换成update语句的片段
    {a:aaa,b:bbb}  =>  a=%s,b=%s,(aaa,bbbb)
    
    "update ttt set a=%s,b=%s where x=%s and y=%s;"
    """
    danger_check=''
    update_column_format=''
    update_args=[]
    opt_limits_sub=opt_limits
    #使用第二个配置条件判断 更改的字段必须等于配置的字段
    logger.debug("origin update keys limits: %s %s" % (list(data.keys()),str(opt_limits_sub)))
    opt_limits_sub,danger_check=get_opt_limits_sub_by_keys(data.keys(),opt_limits_sub,limit_offset=1,match_type='==')  
    logger.debug("update keys limits: %s %s" % (list(data.keys()),str(opt_limits_sub)))
    for k in data:
        if danger_check:
            break
        
        if danger_str and re.search(danger_str,k):
            danger_check='should be normal in column name'
            data=[]
            break
        logger.debug("origin update kv limits: %s %s %s" % (k,data[k],str(opt_limits_sub)))
        opt_limits_sub,danger_check=get_opt_limits_sub_by_kv(k,data[k],opt_limits_sub,limit_offset=1,transfer_value=0)
        logger.debug("origin update kv limits: %s %s %s" % (k,data[k],str(opt_limits_sub)))
        update_column_format += ',`'+k+'`=%s'
        update_args.append(data[k])
    
    update_column_format=update_column_format[1:]
    return danger_check,update_column_format,update_args
   
 
def request_parse(request, args, opt_allow=[]):
    """
    url参数解析
    """
    err_response=''
    data = request.data
    _args=args.split('/')
    opt=_args[-1].lower()
    tag='/'.join(_args[:-1])
    
    params=request.GET              
    
    table_name=''
    opt_limits='' 
    for maps in API_TABLE_MAPPING:
        if maps[0]==tag:
            table_name = maps[1]
            opt_limits = maps[2]  
            
    if not err_response and not table_name:
        err_response = Response({'status':-1,'msg':'table not match','tag':tag})
    
    if not err_response and not opt in opt_limits.keys():
        err_response = Response({'status':-1,'msg':'operate not allow'})
     
    if not err_response and opt_allow and not opt in opt_allow:
        err_response = Response({'status':-1,'msg':'invalid operation'})
   
    if err_response:
        _opt_limits = ''
    else:
        _opt_limits = opt_limits.get(opt)
     
    return err_response,opt,_opt_limits,table_name,params,data


class SimpleCRUD(BASEVIEW):
    '''
    限制
    范围判断只能支持 <= >= 不支持 < >         
    只支持一个层级的条件，不支持复杂的条件，使用视图代替如 where xx=1 or (aa=2 and bb=3)  
    '''
    
    def get(self, request, args = None):
        '''
        select delete
        '''
        connection = connections[DEFAULT_DB]
        
        err_response,opt,opt_limits,table_name,params,data = request_parse(request, args, ['select','delete'])
        if err_response:
            return err_response
        
        danger_check,condition_format,sql_args,select_columns,_=params2condition(params,opt,opt_limits) 
        
        if danger_check:
            return Response({'status':-1,'msg':danger_check})
        
        if opt=='select':
            sql='SELECT %s FROM %s %s' % (select_columns,table_name,condition_format)
        else:
            sql='DELETE FROM %s %s' % (table_name,condition_format)
        
        cursor = connection.cursor()
        try:
            cursor.execute(sql,sql_args)
        except BaseException as e:
            return Response({'status':-1,'sql':sql,'args':sql_args,'msg':str(e)})
        
        result=cursor.fetchall()
        rowcount=cursor.rowcount
        cursor.close()
        
        return Response({'status':1,'sql':sql,'args':sql_args,'result':result,'rowcount':rowcount})
    
    
    
    def post(self, request, args = None):
        '''
        insert update
        '''
        connection = connections[DEFAULT_DB]
        
        err_response,opt,opt_limits,table_name,params,data = request_parse(request, args, ['insert','update'])
        if err_response:
            return err_response
        
        if opt=='insert':
            danger_check,insert_info=dict2insetinfo(data,opt_limits)
            
            if danger_check:
                return Response({'status':-1,'msg':danger_check})
            
            __sql=[]
            
            #with transaction.atomic():
            for _column,_column_format,_sql_args in  insert_info:
                _sql = 'INSERT INTO %s (%s) VALUES (%s);' % (table_name,_column,_column_format)
                __sql.append([_sql,_sql_args])
            
            rowcount=len(__sql)
            sql=str(__sql)
            sql_args=''            
            try:
                cursor = connection.cursor()
                cursor.execute('set autocommit=0')
                for  _sql,_sql_args in __sql:
                    cursor.execute(_sql,_sql_args)
            except BaseException as e:
                connection.rollback()
                cursor.close()
                return Response({'status':-1,'sql':sql,'args':'','msg':str(e)})
            else:
                connection.commit()
                cursor.close()
            
        else:
            danger_check,condition_format,condition_args,_,opt_limits_sub = params2condition(params,opt,opt_limits) 
            if danger_check:
                return Response({'status':-1,'msg':danger_check})
            danger_check1,update_column_format,update_args = dict2updateinfo(data,opt_limits_sub)        
            if danger_check1:
                return Response({'status':-1,'msg':danger_check1})
            
            sql='UPDATE %s SET %s %s;' % (table_name,update_column_format,condition_format)
            sql_args = update_args+condition_args
            
            cursor = connection.cursor()
            try:
                rowcount=cursor.execute(sql,sql_args)
            except BaseException as e:
                connection.rollback()
                cursor.close()
                return Response({'status':-1,'sql':sql,'args':sql_args,'msg':str(e)})
            else:
                connection.commit()
                cursor.close()
        
        return Response({'status':1,'sql':sql,'args':sql_args,'rowcount':rowcount})
        
        
     