FROM python:3.9

# variables
ENV DOCKER_PYTHON_ABK 1

# workdir
WORKDIR /root

# basic software
RUN apt-get -y update; apt-get clean
RUN apt-get -y install nano; apt-get clean

# python packages
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools
RUN pip install --no-cache-dir -r requirements.txt
RUN rm requirements.txt
