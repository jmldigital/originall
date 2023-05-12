#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

echo "продакт депло1йййййййййййййййййййййййййййййййй"
python manage.py migrate --run-syncdb
python manage.py collectstatic --no-input --clear 

exec "$@"