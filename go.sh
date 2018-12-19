#!/usr/bin/env sh

tag=pyospray:latest
ospray_version=1.7.3

download() {
	wget https://github.com/ospray/OSPRay/releases/download/v1.7.3/ospray-1.7.3.x86_64.linux.tar.gz
}

build() {
	docker build -t $tag .
}

run() {
	docker run -i --network host -a stdin -a stdout -a stderr --sig-proxy=true --rm -u $(id -u):$(id -g) -v $PWD:$PWD -w $PWD $tag "$@"

}

python() {
	run python3.7 -u "$@"
}

inspect() {
	docker run -it --rm --entrypoint bash $tag "$@"
}

_=${0##*/}
if [ "$_" = "pyospray" ]; then
	python "$@"
else
	"$@"
fi
