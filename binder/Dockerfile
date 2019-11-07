# Set the base image to beakerx
FROM jupyter/scipy-notebook:1386e2046833 as jupyter

# File Author / Maintainer
MAINTAINER Thomas Schmelzer "thomas.schmelzer@lobnek.com"

# copy the config file
COPY binder/jupyter_notebook_config.py /etc/jupyter/jupyter_notebook_config.py

RUN conda config --env --add pinned_packages 'openjdk>8.0.121'

# install rise and cvxpy
RUN conda install -y -c conda-forge rise cvxpy notebook=6.0.1 beakerx

RUN pip install --no-cache-dir git+http://github.com/lobnek/pyutil.git

# ----------------------------------------------------------------------------------------
FROM jupyter as jupyterlab


RUN conda install -y -c conda-forge jupyterlab && \
    jupyter labextension install @jupyter-widgets/jupyterlab-manager && \
    jupyter labextension install beakerx-jupyterlab && \
    jupyter labextension install @jupyterlab/celltags && \
    jupyter lab build