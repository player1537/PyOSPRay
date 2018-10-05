FROM ubuntu:bionic

RUN apt-get update && apt-get install -y \
	python3.7 \
	python3-pip \
	python3.7-dev \
	swig \
	&& rm -rf /var/lib/apt/lists/*

COPY ospray-1.6.1.x86_64.linux.tar.gz /tmp/
RUN tar xvf /tmp/ospray-1.6.1.x86_64.linux.tar.gz --strip-components=1 -C /usr/

WORKDIR /opt/pyospray
COPY . .
RUN python3.7 -m pip install .

ENTRYPOINT ["python3.7"]
CMD []
