# pull official base image
FROM python:3.10.11-slim-buster

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


# install psycopg2 dependencies
RUN apt-get update 
RUN apt-get upgrade
RUN apt-get -y install postgresql
RUN apt-get install python-psycopg2 -y
RUN apt-get install libpq-dev
RUN apt install -y netcat

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt
RUN python -m pip install psycopg2-binary
RUN pip install pandas

# copy entrypoint.sh
COPY ./entrypoint.prod.sh .
RUN sed -i 's/\r$//g' /usr/src/app/entrypoint.prod.sh
RUN chmod ugo+x /usr/src/app/entrypoint.prod.sh
RUN mkdir /usr/src/app/mediafiles
RUN mkdir /usr/src/app/mediafiles/prices
RUN mkdir /usr/src/app/mediafiles/csv

# copy project
COPY . .

# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.prod.sh"]

