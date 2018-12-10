#!/usr/bin/env sh

tag=pyospray:latest

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

: ${0##*/}
if [ "$_" = "pyospray" ]; then
	python "$@"
else
	"$@"
fi
