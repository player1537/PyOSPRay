#!/usr/bin/env sh

tag=pyospray:latest

_build() {
	docker build -t $tag .
}

_run() {
	docker run -it --rm -v $PWD:$PWD -w $PWD -u $(id -u):$(id -g) $tag "$@"
}

_inspect() {
	docker run -it --rm --entrypoint bash $tag "$@"
}

arg=$1
shift
case "$arg" in
(_build) _build "$@";;
(_run) _run "$@";;
(_inspect) _inspect "$@";;
(_notebook) _notebook "$@";;
(*) _run "$arg" "$@";;
esac
