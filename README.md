简体中文 | [English](./README.en.md)

# simple_crud

[![Python 2.7|3.7](https://img.shields.io/badge/python-2.7%7C3.7-blue.svg)](https://github.com/weideguo/simple_crud) 
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/weideguo/simple_crud/blob/master/LICENSE) 


simple table crud to restful api

api与表CRUD的映射


start
--------------
```shell
#修改配置文件 DATABASES 模块
vim setting/settings.py

#修改配置文件设置api与表的映射关系，如果在settings.py已经设置则不必再设置
vim simple_crud/config.py 

#启动
python manage.py runserver 0.0.0.0:8001
```

