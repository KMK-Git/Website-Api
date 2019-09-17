#!/usr/bin/env bash
params=$(jq -r '.[] | [.ParameterKey, .ParameterValue] | join("=") | sub("[ ]";"\\ ")' params.json)
echo $params
escaped_params=$(printf "%q " "$params")
echo $escaped_params
sam deploy --parameter-overrides $escaped_params --template-file build/packaged.yaml --stack-name website-api