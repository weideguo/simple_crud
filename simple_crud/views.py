# -*- coding: utf-8 -*-

import re
from rest_framework.views import APIView
from rest_framework.response import Response

from django.db import connection,transaction
from django.conf import settings

MyView = APIView

#有些表可能不需要提供如delete操作
API_TABLE_MAP=[('app1/func1', 'a',  {'insert':0,'update':[],'select':[],'delete':[]}),
               ('app1/func2', 'a1', {'insert':2,'update':[],'select':[]}),
               ('app1/func3', 'a2', {}),
]
"""
(where的条件，额外条件)
update where   (a=aaa and b=bbb,[c1,c]) (y=aaa or y=bbb, [c2,c3])  (y>=aaa or y<=bbb, [c2,c3])  (y!=aaa or y!=bbb, [c2,c3])           防止更改额外的字段
delete where
select where   (a=aaa and b=bbb,[c1,c]) (y=aaa or y=bbb, [c2,c3])  (y>=aaa or y<=bbb, [c2,c3])  (y!=aaa or y!=bbb, [c2,c3])           只能查询指定的字段 
insert         更改行数限制  0:无限
"""


DEFAULT_DANGER_STR=getattr(settings, 'SIMPLE_CRUD_DANGER_STR', ';|"|@|`|\'')


def transfer_field(field,or_conn=' OR ',and_conn=' AND '):
    """
    由url的key转换成sql的字段
    """
    break_flag=False
    _k=field
    ao_pre=''
    connector=and_conn
    if field[0]=='|':
        _k=field[1:]
        connector=or_conn
    
    if field[-1] in ['!','>','<']:
        _k=_k[:-1]
        ao_pre=field[-1]
    return break_flag,connector,_k,ao_pre


def transfer_value(value,ao_pre,default_ao='='):
    """
    转换url的value
    """
    break_flag=False
    v=''
    _ao=ao_pre+default_ao
    #print(v,str)
    v=value
    v_format='%s'
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
    danger_check=False
    select_columns='*'
    condition_format=''
    condition_args=[]
    opt_limits_sub=opt_limits                #匹配的子条件 可能下一层条件过滤需要
    
    and_conn=' AND '
    or_conn=' OR '
    default_ao='='   #Arithmetic Operators
    for k in params:
        if danger_check:
            break
        _k=k
        if k=='_' :
            if params[k]:
                #select_columns=params[k]
                for c in params[k]:
                    if danger_str and re.search(danger_str,c):
                        danger_check='should be normal in column name'
                if not danger_check:      
                    select_columns='`'+params[k].replace(',','`,`')+'`'
        elif danger_str and re.search(danger_str,k):
            danger_check='should be normal in column name'
        else:
            break_flag, connector,_k,ao_pre=transfer_field(k)
            if break_flag:
                danger_check=break_flag
                break
            
            break_flag, _ao, v, v_format = transfer_value(params[k],ao_pre)
            if break_flag:
                danger_check=break_flag
                break            
            
            if v:
                condition_args.append(v)
                
            condition_format += connector+('`%s`%s%s' % (_k, _ao, v_format))
            
    if re.match(and_conn,condition_format):
        condition_format=condition_format[len(and_conn):]  
    elif re.match(or_conn,condition_format):
        condition_format=condition_format[len(or_conn):]  
    
    if condition_format:
        condition_format='WHERE '+condition_format
    
    return danger_check, condition_format, condition_args, select_columns,opt_limits_sub

    
def dict2insetinfo(data,opt_limits,danger_str=DEFAULT_DANGER_STR):
    """
    post提交的信息转换成insert语句的片段
    [{a:aaa,b:bbb}]  =>  [["a,b",["aaa","bbb"]]]
    
    "insert into ttt(a,b) values(%s,%s);"
    """
    danger_check=False
    insetinfo=[]
    for d in data:
        _column="" 
        _data=[]
        for k in d:
            if danger_str and re.search(danger_str,k):
                danger_check='should be normal in column name'
                data=[]
                break
            _column += ',`'+k+'`'
            _data.append(d[k])
        _column=_column[1:]
        _column_format=(',%s'*len(_data))[1:]
        insetinfo.append([_column,_column_format,_data])
    
    if opt_limits and len(insetinfo)>opt_limits:
        danger_check='to nuch insert'
    return danger_check,insetinfo
    

def dict2updateinfo(data,opt_limits,danger_str=DEFAULT_DANGER_STR):   
    """ 
    post提交的信息转换成update语句的片段
    {a:aaa,b:bbb}  =>  a=%s,b=%s,(aaa,bbbb)
    
    "update ttt set a=%s,b=%s where x=%s and y=%s;"
    """
    danger_check=False
    update_column_format=''
    update_args=[]

    for k in data:
        if danger_str and re.search(danger_str,k):
            danger_check='should be normal in column name'
            data=[]
            break
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
    opt=_args[-1]
    tag='/'.join(_args[:-1])
    
    params=request.GET              
    
    table_name=''
    opt_limits='' 
    for maps in API_TABLE_MAP:
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


class SimpleCRUD(MyView):
    '''
    限制
    范围判断只能支持 <= >= 不支持 < >         
    反义符号\可能导致不符合预期
    不支持复杂的条件因为实现比较复杂，使用视图代替 xx or (xx and xx)
    
    '''

    def get(self, request, args = None):
        '''
        select delete
        '''
        
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
            if danger_check:
                return Response({'status':-1,'msg':danger_check})
            
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
        
        
     