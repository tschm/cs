FROM tschm/docker:release-0.6

# copy the work folder into the image, hence the notebooks will be available with docker pull from dockerhub
COPY --chown=jovyan:100 ./work $WORK

RUN pip install --no-cache-dir cvxpy git+http://github.com/lobnek/pyutil.git

