#!/usr/bin/env bash
sam deploy --parameter-overrides $(cat parameter_overrides) --template-file build/packaged.yaml --stack-name website-api