#!/usr/bin/python
import glob
import os
import subprocess


def mkdir(directory):
    if directory:
        if not os.path.exists(directory):
            os.makedirs(directory)


d = dict()

with open(".env") as file:
    for row in file:
        a = row.rstrip("\n").split("=")
        d[a[0]] = a[1]

mkdir(directory="pdf")


for f in glob.glob(os.path.join("work", "*.ipynb")):
    file = f.lstrip("work/")
    url = "http://localhost:{PORT}/notebooks/{file}".format(PORT=d["PORT"], file=file)
    out = "/slides/" + file.rstrip(".ipynb") + ".pdf"
    subprocess.check_call('docker run --rm -t -v `pwd`/pdf:/slides --net=host astefanutti/decktape:2.9 rise {url} {out}'.format(url=url, out=out), shell=True)
