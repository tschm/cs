# https://github.com/binder-examples/minimal-dockerfile
FROM docker.io/python:3.9-buster as builder

# install jupyterlab and poetry
RUN pip install --no-cache --upgrade pip && \
    pip install --no-cache poetry

# notebook jupyterlab poetry

# create user with a home directory
ARG NB_USER
ARG NB_UID

ENV USER ${NB_USER}
ENV HOME /home/${NB_USER}

RUN adduser --disabled-password \
    --gecos "Default user" \
    --uid ${NB_UID} \
    ${NB_USER}
WORKDIR ${HOME}

# Don't do this yet
# USER ${USER}

RUN poetry config virtualenvs.create false 

COPY poetry.lock pyproject.toml readme.md ${HOME}

# install the package but without the dev-dependencies and without the root
RUN poetry install --without dev --no-root -vv

# Running poetry here twice seems to be a bad idea but it will help to reduce
# the time for builds. Docker runs much faster if cached layers can be reused.
# We assume that the dashboard package is changed much more frequently than
# the dependencies in pyproject.toml.
COPY ./pycta ${HOME}/pycta

# This is very fast as it only installs the root (e.g. the dashboard) package
RUN poetry install --only-root -vv
#RUN echo "ls -all"

RUN rm poetry.lock pyproject.toml readme.md && \
    rm -rf pycta .cache .config .local

RUN pip uninstall -y poetry

USER ${USER}

