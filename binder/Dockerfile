# Set the base image to jupyter
FROM lobnek/jupyterx:4.8 as jupyter

# copy the work folder into the image, hence the notebooks will be available with docker pull from dockerhub
# need this also for binder...
COPY --chown=jovyan:100 ./work /home/jovyan/work
