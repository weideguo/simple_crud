# -*- coding: utf-8 -*-
from rest_framework.views import APIView

MyView = APIView

#class logger():
#    pass
#
#logger.debug=logger.error=logger.info=print

import sys
import logging
import threading


def simple_logger(name,stream=sys.stdout,level=logging.DEBUG,format="%(asctime)s - %(message)s"):
    """获取简易的日志对象 只是线程安全"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    format = logging.Formatter(format)                      # output format 
    sh = logging.StreamHandler(stream=stream)               
    sh.setFormatter(format)
    logger.addHandler(sh)
    
    return logger

logger=simple_logger('test')

"""
api与表的映射
一个操作可以存在多个限制条件

单个限制条件如：
{'site>':[],'id':[]}, ['site']

每个限制条件
第一个条件为where后的限制
第二个为insert/update post的值，或者select选择的值，即select的字段

空     不限制范围
[]     范围
{}     枚举
''     等值，正则
"""
API_TABLE_MAP=[('app1/func1', 'a',  {'insert':[
                                      (
                                        {}, {'site':[],'id':[10,20]}
                                      ),
                                      (
                                        {}, {'site':'^.{3}$','id':[30,40]}
                                      ),
                                     ],
                                     'update':[
                                       (
                                         {'site':[],'id>':[]},   {'site':[],'id':[]}
                                       ),
                                       (
                                         {'id':[10,100]},        {}
                                       ),
                                     ],
                                     'select':[
                                       (
                                         {'site':[],'id>':[]},      ['site']
                                       ), 
                                       (
                                         {'site':[],'id':[10,20]},  ['site','id']
                                       ), 
                                       (
                                         {'site':[],'|id':[10,20]}, ['site']
                                       ), 
                                       (
                                         {'id':{'null'}},           ['site']
                                       ), 
                                       (
                                         {'id!':{'null'}},          ['site']
                                       ), 
                                       (
                                         {'id!':{'null'}},          []
                                       ), 
                                       (
                                         {},                        ['site']
                                       ),
                                     ],
                                     
                                     'delete':[
                                       (
                                         {'site':[],'id>':[]}, []
                                       ),
                                       (
                                         {'site':[],'id':[10,20]}, []
                                       ), 
                                       (
                                         {'site':[],'|id':[10,20]}, []
                                       ), 
                                       (
                                         {'id':{'null'}}, []
                                       ), 
                                       (
                                         {'id!':{'null'}}, []
                                       ), 
                                                                           
                                     ]}),
               
               
               
               ('app1/func2', 'a1', {'insert':2,'update':[],'select':[]}),
               ('app1/func3', 'a2', {}),
]
