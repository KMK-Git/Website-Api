#!/usr/bin/env bash

STACK_NAME="website-api"
TEMPLATE_FILE="build/template.yaml"
PACKAGED_TEMPLATE_FILE="build/packaged.yaml"
PARAMETERS_FILE="params.json"
EMAIL_TEMPLATES_DIR="./email_templates"
PARAMS=($(jq -r '.[] | [.ParameterKey, .ParameterValue] | "\(.[0])=\(.[1])"' ${PARAMETERS_FILE}))

aws s3 sync "${EMAIL_TEMPLATES_DIR}" "s3://${EMAIL_TEMPLATE_BUCKET}"

sam package --template-file "${TEMPLATE_FILE}" --s3-bucket "${BUILD_ARTIFACT_BUCKET}" --output-template-file "${PACKAGED_TEMPLATE_FILE}"

sam deploy \
  --template-file "${PACKAGED_TEMPLATE_FILE}" \
  --stack-name "${STACK_NAME}" \
  --parameter-overrides ${PARAMS[@]} \
  --no-fail-on-empty-changeset

files=$(aws s3 ls "s3://${BUILD_ARTIFACT_BUCKET}" --recursive | awk '{$1=$2=$3=""; printf "%s ", $0 }' | sed 's/[ \t]\+/ /g')
for file in ${files[*]}
do
  if ! grep -q "$file" "${PACKAGED_TEMPLATE_FILE}"
  then
    aws s3 rm "s3://${BUILD_ARTIFACT_BUCKET}/${file}"
  fi
done