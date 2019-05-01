# Set the base image to jupyter
FROM lobnek/jupyter:v2.8

# File Author / Maintainer
MAINTAINER Thomas Schmelzer "thomas.schmelzer@gmail.com"

# copy the work folder into the image, hence the notebooks will be available with docker pull from dockerhub
COPY --chown=beakerx:beakerx ./work $WORK

# copy everything  (as allowed by .dockerignore) into a tmp folder in image
COPY --chown=beakerx:beakerx . /tmp/pycta

# install the pycta package and all requirements into the image...
RUN pip install --no-cache-dir -r /tmp/pycta/requirements.txt && \
    pip install --no-cache-dir /tmp/pycta && \
    rm -r /tmp/pycta

