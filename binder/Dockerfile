FROM tschm/docker:release-0.4 as jupyter

# copy the work folder into the image, hence the notebooks will be available with docker pull from dockerhub
COPY --chown=jovyan:100 ./work $WORK

RUN pip install --no-cache-dir cvxpy git+http://github.com/lobnek/pyutil.git

# ----------------------------------------------------------------------------------------------------------------------
FROM jupyter as jupyterlab

RUN conda install -y -c conda-forge jupyterlab && \
    conda clean -y --all && \
    jupyter labextension install @jupyter-widgets/jupyterlab-manager && \
    jupyter labextension install beakerx-jupyterlab && \
    jupyter labextension install @jupyterlab/celltags && \
    jupyter lab build
