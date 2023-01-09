# use a docker-stack image
# FROM jupyter/minimal-notebook:a905ff6f6d7b as builder

# https://github.com/binder-examples/minimal-dockerfile
FROM docker.io/python:3.9-slim
# install the notebook package
RUN pip install --no-cache --upgrade pip && \
    pip install --no-cache notebook jupyterlab

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
USER ${USER}


# install poetry
# install curl?
# RUN curl -sSL https://install.python-poetry.org | python3 -

RUN pip install poetry==1.3.1 && \
    poetry config virtualenvs.create true && \
    poetry config virtualenvs.in-project true

COPY poetry.lock pyproject.toml readme.md .

# install the package but without the dev-dependencies and without the root
RUN poetry install --without dev --no-root -vv

# Running poetry here twice seems to be a bad idea but it will help to reduce
# the time for builds. Docker runs much faster if cached layers can be reused.
# We assume that the dashboard package is changed much more frequently than
# the dependencies in pyproject.toml.
COPY ./pycta /home/jovyan/pycta

# This is very fast as it only installs the root (e.g. the dashboard) package
RUN poetry install --only-root -vv
#RUN echo "ls -all"


FROM jupyter/minimal-notebook:a905ff6f6d7b as prod

#COPY --from=builder /home/jovyan /home/jovyan
COPY --from=builder /home/jovyan/.venv /home/jovyan/.venv

#RUN echo $VERSION

#ENTRYPOINT [".venv/bin/python", "adia/backtest.py"]