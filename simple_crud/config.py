# -*- coding: utf-8 -*-

"""
api与表的映射
一个操作可以存在多个限制条件，只需要符合一个限制条件即可正常查询

单个限制条件如：
{'site>':[],'id':[]}, ['site']

每个限制条件
第一个条件为where后的限制
第二个为insert/update post的值，或者select选择的值，即select的字段

空         不限制范围
[]         范围
{}         枚举
字符串     等值，正则
数字       等值

select   where条件限制   select的字段限制
delete   where条件限制   占位符
update   where条件限制   set值的限制
insert   占位符          插入值限制 

"""
#                    url片段,  实际数据库表名, 操作的限制条件
API_TABLE_MAPPING = [('app1/func1', 'a',  {
                                          'select':[
                                            (
                                              {'site':[],'id':[]},        ['id']
                                            ), 
                                            (
                                              {'site':[],'id':[11,20]},   []
                                            ), 
                                            (
                                              {'site':[],'|id':[11,20]},  []
                                            ), 
                                            (
                                              {'site':[],'|id!':[11,20]}, []
                                            ), 
                                            (
                                              {'id':{1,3,4}},             ['site']
                                            ), 
                                            (
                                              {'site':'^.{3}$'},          ['site']
                                            ), 
                                            (
                                              {'site':'null'},            []
                                            ), 
                                            (
                                              {'site!':'null'},           []
                                            ), 
                                            (
                                              {},                         ['site']
                                            ),
                                          ],
                                          'delete':[
                                            (
                                              {'site':[],'id>':[]},       []
                                            ),                            
                                            (                             
                                              {'site':[],'id':[10,20]},   []
                                            ),                            
                                            (                             
                                              {'site':[],'|id':[10,20]},  []
                                            ),                            
                                            (                             
                                              {'id':{'null'}},            []
                                            ),                            
                                            (                             
                                              {'id!':{'null'}},           []
                                            ), 
                                                                                
                                          ],                                    
                                          'update':[
                                            (
                                              {'site':[],'id':[]},   {'site':[],'id':[]}
                                            ),
                                            (
                                              {'id':[10,100]},       {}
                                            ),
                                          ],                                     
                                          'insert':[
                                            (
                                              {}, {'site':[],'id':[10,20]}
                                            ),    
                                            (     
                                              {}, {'site':'^.{3}$','id':[30,40]}
                                            ),    
                                            (     
                                              {}, {'id':[100,200]}
                                            ),    
                                            (     
                                              {}, {'site':{'aaaa','bbbb','cccc'},'id':[201,300]}
                                            ),
                                          ],
                                          
                                          }),
               
               
               
               ('app1/func2', 'a1', {'insert':2,'update':[],'select':[],'delete':[]}),
               ('app1/func3', 'a2', {'insert':2,'update':[],'select':[]}),
]
