# https://github.com/binder-examples/minimal-dockerfile
FROM docker.io/python:3.9 as builder

# update pip
RUN pip install --no-cache-dir --upgrade pip 

    
# create user with a home directory
ARG NB_USER
ARG NB_UID

ENV USER ${NB_USER}
ENV HOME /home/${NB_USER}

RUN adduser --disabled-password --gecos "Default user" --uid ${NB_UID} ${NB_USER}

WORKDIR ${HOME}

COPY . ${HOME}
RUN pip install --no-cache-dir -r ${HOME}/requirements.txt

USER ${USER}
