# Set the base image to jupyter
FROM tschm/jupyter:1.0.0 as jupyter

# copy the work folder into the image, hence the notebooks will be available with docker pull from dockerhub
# need this also for binder...and for windows
RUN conda install -y -c conda-forge beakerx=1.4.1  && \
    conda clean -y --all


COPY --chown=jovyan:100 ./work /home/jovyan/work
