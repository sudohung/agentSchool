#!/bin/sh
# 生成图片（可选）并通过飞书发送。POSIX sh（busybox ash）兼容。
# 用法见 SKILL.md；帮助：generate-and-send.sh --help
set -eu

GEN_ENDPOINT="https://token-plan.maas.qianwenaiapi.com/api/v1/services/aigc/multimodal-generation/generation"
FS_BASE="https://open.feishu.cn/open-apis"
ENV_IMAGE="${ENV_IMAGE:-/workspace/.env}"
ENV_FEISHU="${ENV_FEISHU:-/root/.config/agentConfig/feishu.env}"
TMP_DIR="${TMPDIR:-/tmp/opencode}"
DEFAULT_RECEIVER="${FEISHU_DEFAULT_RECEIVER:-ou_876aae79dd601923ba73d825d5e1d155}"

MODEL="qwen-image-3.0-pro"
SIZE="1024*1024"
N=1
PROMPT=""
OUT=""
SEED=""
NEGATIVE=""
IMAGE=""
TO=""
TO_TYPE="open_id"
DO_GENERATE=1
DO_SEND=1
FILES=""

die() { echo "错误: $*" >&2; exit 1; }
log() { echo "· $*" >&2; }

usage() {
  cat <<'EOF'
用法:
  generate-and-send.sh --prompt "描述" [选项]

生成:
  --prompt TEXT        图片描述（必填，除非使用 --image）
  --model NAME         默认 qwen-image-3.0-pro
  --size WxH           默认 1024*1024（16:9→1664*928，9:16→928*1664，4:3→1472*1104，3:4→1104*1472）
  --n NUM              生成张数，默认 1
  --seed INT           固定种子（可选，未指定则不传）
  --negative TEXT      负向提示（可选，未指定则不传）
  --out PATH           输出文件，默认 ./generated_<时间戳>.png
  --no-generate        跳过生成，直接用 --image 发送
  --image PATH         已有图片（与 --no-generate 配合，也可用于先预览）

发送:
  --to ID              接收人 open_id 或群 chat_id（默认应用所属用户）
  --to-type TYPE       open_id | chat_id，默认 open_id
  --no-send            只生成，不上传不发送

  -h, --help           显示帮助
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --prompt)      PROMPT="$2"; shift 2 ;;
    --model)       MODEL="$2"; shift 2 ;;
    --size)        SIZE="$2"; shift 2 ;;
    --n)           N="$2"; shift 2 ;;
    --seed)        SEED="$2"; shift 2 ;;
    --negative)    NEGATIVE="$2"; shift 2 ;;
    --out)         OUT="$2"; shift 2 ;;
    --image)       IMAGE="$2"; shift 2 ;;
    --to)          TO="$2"; shift 2 ;;
    --to-type)     TO_TYPE="$2"; shift 2 ;;
    --no-generate) DO_GENERATE=0; shift ;;
    --no-send)     DO_SEND=0; shift ;;
    -h|--help)     usage; exit 0 ;;
    *) die "未知参数: $1（用 --help 查看用法）" ;;
  esac
done

mkdir -p "$TMP_DIR"
if [ "$DO_GENERATE" = 1 ] && [ -z "$PROMPT" ]; then die "缺少 --prompt"; fi
if [ -n "$IMAGE" ] && [ ! -f "$IMAGE" ]; then die "图片不存在: $IMAGE"; fi

is_image() { # 校验 PNG / JPEG 魔数
  [ -s "$1" ] || return 1
  _m=$(node -e 'const b=require("fs").readFileSync(process.argv[1]);const h=b.slice(0,8).toString("hex");process.stdout.write(h.startsWith("89504e47")?"png":h.startsWith("ffd8ff")?"jpg":"other")' "$1")
  [ "$_m" = "png" ] || [ "$_m" = "jpg" ]
}

# ---------- 1. 生成 ----------
if [ "$DO_GENERATE" = 1 ]; then
  [ -f "$ENV_IMAGE" ] || die "缺少 $ENV_IMAGE（需要 ANTHROPIC_AUTH_TOKEN）"
  set -a; . "$ENV_IMAGE"; set +a
  [ -n "${ANTHROPIC_AUTH_TOKEN:-}" ] || die "ANTHROPIC_AUTH_TOKEN 未配置"

  PAYLOAD="$TMP_DIR/imggen_payload.$$.json"
  node -e '
    const [prompt, model, size, n, seed, neg, out] = process.argv.slice(1);
    const body = { model, input: { messages: [{ role: "user", content: [{ text: prompt }] }] },
                   parameters: { size, n: Number(n), prompt_extend: false, watermark: false } };
    if (seed !== "") body.parameters.seed = Number(seed);
    if (neg !== "") body.parameters.negative_prompt = neg;
    require("fs").writeFileSync(out, JSON.stringify(body));
  ' "$PROMPT" "$MODEL" "$SIZE" "$N" "$SEED" "$NEGATIVE" "$PAYLOAD"

  RESP="$TMP_DIR/imggen_resp.$$.json"
  log "生成中（model=$MODEL size=$SIZE n=$N）…"
  code=$(curl -sS -o "$RESP" -w '%{http_code}' -X POST "$GEN_ENDPOINT" \
    -H "Authorization: Bearer $ANTHROPIC_AUTH_TOKEN" \
    -H "Content-Type: application/json" -d @"$PAYLOAD") || { rm -f "$PAYLOAD"; die "请求生成接口失败"; }
  rm -f "$PAYLOAD"
  if [ "$code" != "200" ]; then
    echo "接口返回 HTTP $code：" >&2
    head -c 800 "$RESP" >&2; echo >&2
    die "生成失败"
  fi

  URLS=$(node -e '
    const j = require(process.argv[1]);
    if (j.code && j.code !== 0) { console.error(JSON.stringify(j).slice(0, 500)); process.exit(2); }
    const urls = (j.output?.choices ?? []).flatMap(c => (c.message?.content ?? []))
      .filter(x => x.image).map(x => x.image);
    if (!urls.length) { console.error(JSON.stringify(j).slice(0, 500)); process.exit(3); }
    process.stdout.write(urls.join("\n"));
  ' "$RESP") || { rm -f "$RESP"; die "生成失败（返回中未找到图片 URL，详见上方输出）"; }
  rm -f "$RESP"

  i=0
  printf '%s\n' "$URLS" | while IFS= read -r url; do
    [ -n "$url" ] || continue
    i=$((i+1))
    if [ -n "$OUT" ]; then
      if [ "$i" = 1 ]; then target="$OUT"; else target="${OUT%.*}_$i.${OUT##*.}"; fi
    else
      target="./generated_$(date +%Y%m%d_%H%M%S).png"
    fi
    [ -e "$target" ] && target="${target%.*}_$(date +%H%M%S).${target##*.}"
    curl -sS -o "$target" "$url" || die "下载失败: $url"
    is_image "$target" || die "下载的文件不是有效图片: $target（URL: $url）"
    printf '%s\n' "$target" >> "$TMP_DIR/files.$$"
    log "已下载 $target（$(wc -c < "$target" | tr -d ' ') 字节）"
  done
  FILES=$(cat "$TMP_DIR/files.$$" 2>/dev/null || true)
  rm -f "$TMP_DIR/files.$$"
  [ -n "$FILES" ] || die "没有下载到任何图片"
else
  [ -n "$IMAGE" ] || die "--no-generate 需要配合 --image"
  FILES="$IMAGE"
fi

# ---------- 2. 上传到飞书 ----------
if [ "$DO_SEND" = 0 ]; then
  echo
  echo "完成（已跳过发送）"
  printf '%s\n' "$FILES" | while IFS= read -r f; do
    [ -n "$f" ] || continue
    echo "  图片: $(cd "$(dirname "$f")" && pwd)/$(basename "$f")"
  done
  exit 0
fi

[ -f "$ENV_FEISHU" ] || die "缺少 $ENV_FEISHU（需要 FEISHU_APP_ID / FEISHU_APP_SECRET）"
set -a; . "$ENV_FEISHU"; set +a
if [ -z "${FEISHU_APP_ID:-}" ] || [ -z "${FEISHU_APP_SECRET:-}" ]; then die "飞书应用凭证不完整"; fi

TOKEN=$(curl -sS -X POST "$FS_BASE/auth/v3/tenant_access_token/internal" \
  -H "Content-Type: application/json" \
  -d "{\"app_id\":\"$FEISHU_APP_ID\",\"app_secret\":\"$FEISHU_APP_SECRET\"}" \
  | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{const j=JSON.parse(s);if(j.code!==0){console.error("取 token 失败: "+j.code+" "+j.msg);process.exit(1)}process.stdout.write(j.tenant_access_token)})') \
  || die "获取 tenant_access_token 失败"
log "已获取飞书 token"

RECEIVER="${TO:-$DEFAULT_RECEIVER}"

printf '%s\n' "$FILES" | while IFS= read -r f; do
  [ -n "$f" ] || continue
  IMG_KEY=$(curl -sS -X POST "$FS_BASE/im/v1/images" -H "Authorization: Bearer $TOKEN" \
    -F "image_type=message" -F "image=@$f" \
    | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{const j=JSON.parse(s);if(j.code!==0){console.error("上传失败: "+j.code+" "+j.msg);process.exit(1)}process.stdout.write(j.data.image_key)})') \
    || die "上传图片到飞书失败: $f"
  log "已上传 $(basename "$f") → $IMG_KEY"

  BODY="$TMP_DIR/fs_send.$$.json"
  node -e '
    const [recv, key, out] = process.argv.slice(1);
    require("fs").writeFileSync(out, JSON.stringify({
      receive_id: recv, msg_type: "image",
      content: JSON.stringify({ image_key: key })
    }));
  ' "$RECEIVER" "$IMG_KEY" "$BODY"

  RESULT=$(curl -sS -X POST "$FS_BASE/im/v1/messages?receive_id_type=$TO_TYPE" \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d @"$BODY")
  rm -f "$BODY"

  printf '%s' "$RESULT" | node -e '
    let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{
      const j=JSON.parse(s);
      if(j.code!==0){console.error("发送失败: code="+j.code+" msg="+j.msg);process.exit(1)}
      console.error("已发送 message_id="+j.data.message_id+" chat_id="+(j.data.chat_id||"-"));
    })' || die "发送飞书消息失败"
done

echo
echo "完成"
printf '%s\n' "$FILES" | while IFS= read -r f; do
  [ -n "$f" ] || continue
  echo "  图片: $(cd "$(dirname "$f")" && pwd)/$(basename "$f")"
done
if [ "$DO_GENERATE" = 1 ]; then
  echo "  参数: model=$MODEL size=$SIZE n=$N seed=${SEED:-未指定} negative=${NEGATIVE:-未指定} prompt_extend=false watermark=false"
fi
echo "  接收: $RECEIVER ($TO_TYPE)"