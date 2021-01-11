#启动
/data/python36/bin/python3 manage.py runserver 0.0.0.0:8001



CREATE TABLE `a` (
  `id` int(11) DEFAULT NULL,
  `site` varchar(50) DEFAULT NULL
)


####################select
#
curl 'http://127.0.0.1:8001/api/v1/app1/func1/select?id=10'  
# limit以及过滤字段
curl 'http://127.0.0.1:8001/api/v1/app1/func1/select?id=10&_=site&__=10,1' 
#>= <= !=
curl 'http://127.0.0.1:8001/api/v1/app1/func1/select?site>=bm_0001'  
curl 'http://127.0.0.1:8001/api/v1/app1/func1/select?site<=bm_0001'  
curl 'http://127.0.0.1:8001/api/v1/app1/func1/select?site!=bm_0001'  

#like not like 存在%时
curl 'http://127.0.0.1:8001/api/v1/app1/func2/select?site=%aa' 
curl 'http://127.0.0.1:8001/api/v1/app1/func2/select?site=a%a' 
curl 'http://127.0.0.1:8001/api/v1/app1/func2/select?site=aa%' 
curl 'http://127.0.0.1:8001/api/v1/app1/func2/select?site!=%aa' 

#null
curl 'http://127.0.0.1:8001/api/v1/app1/func1/select?site=null'  
#not null
curl 'http://127.0.0.1:8001/api/v1/app1/func1/select?site!=null'  

#or
curl 'http://127.0.0.1:8001/api/v1/app1/func1/select?id=111&|site=aaa'  
curl 'http://127.0.0.1:8001/api/v1/app1/func1/select?id=111&|site!=aaa' 




####################delete

curl 'http://127.0.0.1:8001/api/v1/app1/func1/delete?id>=100'


####################update

curl "http://127.0.0.1:8001/api/v1/app1/func1/update?id=222" -d "{\"id\":333,\"site\":\"444\"}" -H "Content-Type:application/json"

curl "http://127.0.0.1:8001/api/v1/app1/func1/update?id>=111" -d "{\"id\":333,\"site\":\"444\"}" -H "Content-Type:application/json"




####################insert

curl "http://127.0.0.1:8001/api/v1/app1/func1/insert" -d "[{\"id\":12,\"sitexxx\":\"444\"}]" -H "Content-Type:application/json"

curl "http://127.0.0.1:8001/api/v1/app1/func1/insert" -d "[{\"id\":12,\"sitexxx\":\"444\"},{\"id\":13}]" -H "Content-Type:application/json"

curl "http://127.0.0.1:8001/api/v1/app1/func1/insert" -d "[{\"id\":12,\"site\":\"444\"},{\"id\":13,\"site\":\"bbb\"}]" -H "Content-Type:application/json"

curl "http://127.0.0.1:8001/api/v1/app1/func1/insert" -d "[{\"id\":12,\"site\":\"444\"}]" -H "Content-Type:application/json"

curl "http://127.0.0.1:8001/api/v1/app1/func1/insert" -d "[{\"id\":11}]" -H "Content-Type:application/json"

curl "http://127.0.0.1:8001/api/v1/app1/func1/insert" -d "[{\"id\":1100}]" -H "Content-Type:application/json"

curl "http://127.0.0.1:8001/api/v1/app1/func1/insert" -d "[{\"id\":300,\"site\":\"444\"}]" -H "Content-Type:application/json"






