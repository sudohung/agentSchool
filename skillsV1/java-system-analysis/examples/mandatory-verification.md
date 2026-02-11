# Mandatory verification examples for java-system-analysis

This file contains the example automation snippets referenced in the SKILL.md under "强制校验：确保引用的代码在项目中存在".

Bash example (verify-references.sh):

```bash
#!/usr/bin/env bash
# verify-references.sh
# 输入: refs.txt（文件内每行一个要验证的字符串或相对路径）
# 输出: 如果存在缺失项则写入 missing_references.txt 并以非零退出码返回

actions=("git grep -n" "rg -n")
refs_file="$1"
missing_file="missing_references.txt"
: > "$missing_file"
while IFS= read -r ref || [ -n "$ref" ]; do
  if [ -z "$ref" ]; then
    continue
  fi
  found=0
  for cmd in "${actions[@]}"; do
    if $cmd "$ref" >/dev/null 2>&1; then
      found=1
      break
    fi
  done
  if [ "$found" -eq 0 ]; then
    echo "$ref" >> "$missing_file"
  fi
done < "$refs_file"
if [ -s "$missing_file" ]; then
  echo "Missing references found (see $missing_file)"
  exit 2
else
  echo "All references verified."
  exit 0
fi
```

PowerShell example (Verify-References.ps1):

```powershell
# Verify-References.ps1
# 输入: refs.txt，每行为一个待验证的字符串或相对路径
# 输出: 找到缺失项则写入 mandatory-missing.txt 并以非零退出码返回
param(
    [string]$RefsFile = "refs.txt",
    [string]$MissingFile = "mandatory-missing.txt"
)
New-Item -Force -Path $MissingFile -ItemType File | Out-Null
foreach ($ref in Get-Content $RefsFile) {
    if ([string]::IsNullOrWhiteSpace($ref)) { continue }
    $found = $false
    # 首先尝试 git grep（如果可用）
    try {
        $out = git grep -n -- "$ref" 2>$null
        if ($out) { $found = $true }
    } catch {
        # git grep 不可用则使用 PowerShell 检索
        $matches = Get-ChildItem -Recurse -File -ErrorAction SilentlyContinue | Select-String -Pattern $ref -List -SimpleMatch
        if ($matches) { $found = $true }
    }
    if (-not $found) {
        Add-Content -Path $MissingFile -Value $ref
    }
}
if ((Get-Item $MissingFile).Length -gt 0) {
    Write-Host "Some referenced items are missing. See $MissingFile" -ForegroundColor Yellow
    exit 2
} else {
    Write-Host "All referenced items verified." -ForegroundColor Green
    exit 0
}
```
