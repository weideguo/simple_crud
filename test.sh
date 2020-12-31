#启动
/data/python3.6/bin/python3 manage.py runserver 0.0.0.0:8001


curl "http://127.0.0.1:8001/api/v1/MyView"


curl "http://127.0.0.1:8001/api/v1/a?a=aaa"

####################select
#< > !
curl 'http://127.0.0.1:8001/api/v1/app1/func1/select?site=bm_0001'  
curl 'http://127.0.0.1:8001/api/v1/app1/func1/select?site>=bm_0001'  
curl 'http://127.0.0.1:8001/api/v1/app1/func1/select?site<=bm_0001'  
curl 'http://127.0.0.1:8001/api/v1/app1/func1/select?site!=bm_0001'  


#null
curl 'http://127.0.0.1:8001/api/v1/app1/func1/select?a=aaa&b=null'  

#is not null
curl 'http://127.0.0.1:8001/api/v1/app1/func1/select?a=aaa&b!=null'  

#or
curl 'http://127.0.0.1:8001/api/v1/app1/func1/select?a=aaa&|b!=null'  

#column
curl 'http://127.0.0.1:8001/api/v1/app1/func1/select?a=aaa&|b!=null&_a,b'  


curl "http://127.0.0.1:8001/api/v1/app1/func1/select?a=aaa&b=bbb" 


####################delete

curl 'http://127.0.0.1:8001/api/v1/app1/func1/delete?id>=100'


####################update

curl "http://127.0.0.1:8001/api/v1/app1/func1/update?id=222" -d "{\"id\":\"333\",\"site\":\"444\"}" -H "Content-Type:application/json"



curl "http://127.0.0.1:8001/api/v1/app1/func1/update?id>=111" -d "{\"id\":\"333\",\"site\":\"444\"}" -H "Content-Type:application/json"

curl "http://127.0.0.1:8001/api/v1/app1/func1/update?a=aaa" -d "{\"username\":\"admin\",\"password\":\"weideguo\"}" -H "Content-Type:application/json"





####################insert

curl "http://127.0.0.1:8001/api/v1/app1/func1/insert" -d "[{\"id\":\"333\",\"sicccte\":\"444\"},{\"id\":\"444\"}]" -H "Content-Type:application/json"


curl "http://127.0.0.1:8001/api/v1/app1/func1/insert" -d "[{\"id\":555},{\"id\":\"333\",\"sitexxx\":\"444\"},{\"id\":\"444\"}]" -H "Content-Type:application/json"

curl "http://127.0.0.1:8001/api/v1/app1/func1/insert" -d "[{\"id\":555},{\"id\":\"333\",\"site\":\"444\"},{\"id\":\"444\"}]" -H "Content-Type:application/json"








