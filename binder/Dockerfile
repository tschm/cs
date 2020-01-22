# Set the base image to jupyter
FROM jupyter/minimal-notebook:7a0c7325e470 as jupyter

# File Author / Maintainer
MAINTAINER Thomas Schmelzer "thomas.schmelzer@gmail.com"

# copy the config.ini file
COPY /binder/jupyter_notebook_config.py /etc/jupyter/jupyter_notebook_config.py


RUN conda install -y -c conda-forge nomkl pandas cvxpy beakerx && \
    conda clean -y --all

RUN pip install --no-cache-dir cvxpy git+http://github.com/lobnek/pyutil.git

# copy the work folder into the image, hence the notebooks will be available with docker pull from dockerhub
COPY --chown=jovyan:100 ./work /home/jovyan/work
