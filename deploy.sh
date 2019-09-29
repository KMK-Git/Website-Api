#!/usr/bin/env bash
aws s3 sync ./email_templates "s3://$EMAIL_TEMPLATE_BUCKET"
oldfiles=$(aws s3 ls s3://$BUILD_ARTIFACT_BUCKET --recursive | awk '{$1=$2=$3=""; printf "%s ", $0 }' | sed 's/[ \t]\+/ /g')
sam package --template-file build/template.yaml --s3-bucket $BUILD_ARTIFACT_BUCKET --output-template-file build/packaged.yaml
STACK_NAME="website-api"
TEMPLATE="build/packaged.yaml"
PARAMETERS_FILE="params.json"
PARAMS=($(jq -r '.[] | [.ParameterKey, .ParameterValue] | "\(.[0])=\(.[1])"' ${PARAMETERS_FILE}))
sam deploy \
  --template-file "${TEMPLATE}" \
  --stack-name "${STACK_NAME}" \
  --parameter-overrides ${PARAMS[@]} \
  --no-fail-on-empty-changeset
for file in ${oldfiles[*]}
do
	aws s3 rm "s3://$BUILD_ARTIFACT_BUCKET/$file" --dryrun
done