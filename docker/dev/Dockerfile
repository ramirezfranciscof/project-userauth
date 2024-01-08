################################################################################
# MULTISTAGE 1 - BUILD
################################################################################
FROM ubuntu:20.04

# avoid stuck build due to user prompt
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install --no-install-recommends -y \
    git vim screen curl \
    python3.9 \
    python3.9-dev \
    python3.9-venv \
    python3-pip \
    python3-wheel \
    build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# create and activate virtual environment
# using final folder name to avoid path issues with packages
RUN python3.9 -m venv /home/root/venv
ENV VIRTUAL_ENV=/home/root/venv
ENV PATH="/home/root/venv/bin:$PATH"

# make sure all messages always reach console
ENV PYTHONUNBUFFERED=1

# install requirements
WORKDIR /home/root/app
COPY . .

RUN pip3 install --upgrade pip
RUN python3 -m pip install --upgrade setuptools
#RUN pip3 install --no-cache-dir wheel
#RUN pip3 install --no-cache-dir -r requirements.txt
#RUN pip3 install jupyterlab
RUN pip3 install -r requirements.txt
RUN pip3 install -e .[dev]

# NOTE: This does not actually publish the port, it is more a type of
# documentation (using docker run with the `-P` flag publishes all the
# exposed ports, otherwise manually use `-p <cont_port>:<host_port>`).
EXPOSE 8000
EXPOSE 8888

ENV SHELL=/bin/bash
CMD ["jupyter-lab","--ip=0.0.0.0","--no-browser","--allow-root"]
#CMD ["jupyter-lab","--ip=0.0.0.0","--port=8888","--no-browser","--allow-root"]
#CMD ["userauth","server", "start"]
################################################################################
