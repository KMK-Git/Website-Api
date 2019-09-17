#!/usr/bin/env bash
STACK_NAME="website-api"
TEMPLATE="build/packaged.yaml"
PARAMETERS_FILE="params.json"
PARAMS=($(jq -r '.[] | [.ParameterKey, .ParameterValue] | "\"\(.[0])=\(.[1])\""' ${PARAMETERS_FILE}))
echo ${PARAMS[@]}
sam deploy \
  --template-file "${TEMPLATE}" \
  --stack-name "${STACK_NAME}" \
  --parameter-overrides ${PARAMS[@]}
