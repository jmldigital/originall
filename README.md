# originall

задать права на выполнение перед развертыванием, в докер файле есть эта команда не выполняется, не знаю почему

```chmod ugo+x entrypoint.prod.sh ```


[.env](https://github.com/jmldigital/originall/blob/master/.env)  прописываем ip сервера  
```DJANGO_ALLOWED_HOSTS=77.232.139.126 localhost 127.0.0.1 [::1]```
