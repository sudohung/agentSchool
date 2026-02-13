#!/usr/bin/env bash

pwd

echo 'on push  script'

echo 'installing opencode-ai'

npm install -g opencode-ai

echo 'set api key'

export OPENCODE_API_KEY="sk-sp-de6e887faf1f49acbad120766050fdd9"

mkdir -p ~/.config/opencode
cp ./cicd/opencode.json ~/.config/opencode/opencode.json

echo 'install opencode-ai finish'


opencode run '你好' --agent plan --model CodingPlan/qwen3-max-2026-01-23


echo 'run opencode-ai finish'

