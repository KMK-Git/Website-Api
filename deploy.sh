#!/usr/bin/env bash
params=$(jq -r '.[] | [.ParameterKey, .ParameterValue] | join("=")' params.json)
escaped_params=""
for param in $params; do
	escaped_params+=$(printf "%q " $param)
done
sam deploy --parameter-overrides $escaped_params --template-file build/packaged.yaml --stack-name website-api