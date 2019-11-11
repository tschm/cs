
# Set the base image to jupyter
FROM tschm/docker:release-0.4 
#as jupyter

# copy the work folder into the image, hence the notebooks will be available with docker pull from dockerhub
COPY --chown=jovyan:100 ./work $WORK

## Set the base image to beakerx
#FROM jupyter/scipy-notebook:1386e2046833 as jupyter

# File Author / Maintainer
#MAINTAINER Thomas Schmelzer "thomas.schmelzer@lobnek.com"


# install rise and cvxpy
#RUN conda install -y cvxpy

RUN pip install --no-cache-dir cvxpy git+http://github.com/lobnek/pyutil.git

# ----------------------------------------------------------------------------------------
#FROM jupyter as jupyterlab
#
#
#RUN conda install -y -c conda-forge jupyterlab && \
#    jupyter labextension install @jupyter-widgets/jupyterlab-manager && \
#    jupyter labextension install beakerx-jupyterlab && \
#    jupyter labextension install @jupyterlab/celltags && \
#    jupyter lab build
