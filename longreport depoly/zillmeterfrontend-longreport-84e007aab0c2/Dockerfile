FROM python:3.9.9
MAINTAINER Hossein Shemshadi & Mahdi Farrokhpey

RUN apt-get update -y
RUN apt-get install -y unoconv
RUN sed -i "s/#!\/usr\/bin\/env python3/#!\/usr\/bin\/python3/" /usr/bin/unoconv

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt

COPY . .
RUN mkdir out
WORKDIR /app/src

EXPOSE 5000
CMD ["python", "/app/src/controller.py"]