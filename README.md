# originall

# выполнить после git clone, в докер файле есть эта команда, но она по чему-то не выполняется
chmod ugo+x entrypoint.prod.sh

# .env прописываем ip сервера  
DJANGO_ALLOWED_HOSTS=77.232.139.126 localhost 127.0.0.1 [::1]
