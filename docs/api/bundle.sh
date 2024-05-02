#!/bin/zsh
docker run --rm -v $PWD:/spec redocly/cli bundle openapi.yaml > openapi-bundled.yaml