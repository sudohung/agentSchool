#!/usr/bin/env bash

echo 'on auto script'

opencode run '修复提交代码的严重问题并提交push' --agent build --model CodingPlan/qwen3-max-2026-01-23 -c

echo 'fix commit finish'


