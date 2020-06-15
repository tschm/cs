# Set the base image to jupyter
FROM tschm/jupyter:1.2.0 as jupyter

# copy the work folder into the image, hence the notebooks will be available with docker pull from dockerhub
# need this also for binder...and for windows
RUN pip install matplotlib

COPY --chown=jovyan:100 ./work $WORK
