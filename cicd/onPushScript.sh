#!/usr/bin/env bash

pwd

echo 'on push script'

echo 'install opencode-ai'

npm install -g opencode-ai

export OPENCODE_API_KEY="sk-sp-de6e887faf1f49acbad120766050fdd9"

mkdir -p ~/.config/opencode
cp ./cicd/opencode.json ~/.config/opencode/opencode.json

echo 'install opencode-ai finish'

opencode run '你好' --agent plan --model CodingPlan/qwen3-max-2026-01-23

echo 'check opencode-ai finish'

echo 'start check commit'

opencode run '检查刚刚最新提交的代码，忽略cicd文件夹；如果有严重问题则进行修复并提交一个merge request' --agent build --model CodingPlan/qwen3-max-2026-01-23

echo 'check commit finish'


