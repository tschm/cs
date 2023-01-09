# https://github.com/binder-examples/minimal-dockerfile
FROM docker.io/python:3.9-buster as builder

# install jupyterlab and poetry
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir poetry
    #&& \
    #poetry config virtualenvs.create true && \
    #poetry config virtualenvs.in-project true && \
    #poetry config cache-dir ".cache" && \
    #poetry config virtualenvs.path ".venv"

# create user with a home directory
ARG NB_USER
ARG NB_UID

ENV USER ${NB_USER}
ENV HOME /home/${NB_USER}

#WORKDIR ${HOME}
#COPY . ${HOME}

RUN adduser --disabled-password \
    --gecos "Default user" --uid ${NB_UID} \
    ${NB_USER}

USER ${USER}

WORKDIR ${HOME}
COPY . ${HOME}

RUN poetry config virtualenvs.create true && \
    poetry config virtualenvs.in-project true && \
    poetry config cache-dir ".cache" && \
    poetry config virtualenvs.path ".venv"



# install jupyterlab and poetry
# RUN pip install --no-cache --upgrade pip && \
#     pip install --no-cache poetry && \
#     poetry config virtualenvs.create true && \
#     poetry config virtualenvs.in-project true

# notebook jupyterlab poetry


USER ${USER}
    
RUN poetry install -vv 
#    #&& \
#    #rm poetry.lock pyproject.toml readme.md && \
#    #rm -rf pycta .cache .config .local && \
#    #pip uninstall -y poetry

USER ${USER}

