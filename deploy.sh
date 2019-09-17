#!/usr/bin/env bash
STACK_NAME="website-api"
PARAMETERS_FILE="params.json"
PARAMS=($(jq -r '.[] | [.ParameterKey, .ParameterValue] | "\(.[0])=\(.[1])"' ${PARAMETERS_FILE}))
echo $PARAMS
echo ${PARAMS[@]}
sam deploy \
  --stack-name "${STACK_NAME}" \
  --parameter-overrides ${PARAMS[@]}
