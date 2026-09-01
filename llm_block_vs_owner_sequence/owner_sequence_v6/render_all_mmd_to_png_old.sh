#!/usr/bin/env bash

set -uo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
input_dir=${1:-"${script_dir}/mmd"}
output_dir=${2:-"${script_dir}/png"}

mermaid_version=11.17.2
mermaid_cli_version=11.16.0
png_width=${PNG_WIDTH:-2400}
png_scale=${PNG_SCALE:-1}

if ! command -v npm >/dev/null 2>&1; then
  echo "错误：未找到 npm。" >&2
  exit 2
fi

chrome_bin=${CHROME_BIN:-}
if [[ -z "$chrome_bin" ]]; then
  for candidate in google-chrome google-chrome-stable chromium chromium-browser; do
    if command -v "$candidate" >/dev/null 2>&1; then
      chrome_bin=$(command -v "$candidate")
      break
    fi
  done
fi

if [[ -z "$chrome_bin" || ! -x "$chrome_bin" ]]; then
  echo "错误：未找到 Chrome/Chromium。可通过 CHROME_BIN=/path/to/chrome 指定。" >&2
  exit 2
fi

if [[ ! -d "$input_dir" ]]; then
  echo "错误：输入目录不存在：$input_dir" >&2
  exit 2
fi

mkdir -p -- "$output_dir"
temp_dir=$(mktemp -d)
trap 'rm -rf -- "$temp_dir"' EXIT

mapfile -d '' mmd_files < <(
  find "$input_dir" -maxdepth 1 -type f -name '*.mmd' -print0 | sort -z
)

if (( ${#mmd_files[@]} == 0 )); then
  echo "错误：输入目录中没有 .mmd 文件：$input_dir" >&2
  exit 2
fi

export PUPPETEER_SKIP_DOWNLOAD=true
export PUPPETEER_EXECUTABLE_PATH="$chrome_bin"

tool_dir="${temp_dir}/tooling"
echo "正在准备固定版本 Mermaid 工具链……"
if ! npm install \
    --prefix "$tool_dir" \
    --no-save \
    --ignore-scripts \
    --prefer-offline \
    --no-audit \
    --no-fund \
    --silent \
    "mermaid@${mermaid_version}" \
    "@mermaid-js/mermaid-cli@${mermaid_cli_version}"; then
  echo "错误：Mermaid 工具链安装失败。" >&2
  exit 2
fi
mmdc="${tool_dir}/node_modules/.bin/mmdc"

echo "Mermaid engine : ${mermaid_version}"
echo "Mermaid CLI    : ${mermaid_cli_version}"
echo "Chrome         : ${chrome_bin}"
echo "Input          : ${input_dir}"
echo "Output         : ${output_dir}"
echo "PNG width      : ${png_width}"
echo "PNG scale      : ${png_scale}"
echo

success_count=0
failure_count=0

for source_file in "${mmd_files[@]}"; do
  filename=$(basename -- "$source_file")
  stem=${filename%.mmd}
  render_input=$source_file
  output_file="${output_dir}/${stem}.png"

  if head -n 1 "$source_file" | grep -Eq '^%%[[:space:]]+\{init:'; then
    render_input="${temp_dir}/${filename}"
    sed '1s/^%%[[:space:]]\+{init:/%%{init:/' "$source_file" > "$render_input"
    echo "警告：${filename} 第 1 行存在 '%% {init'，使用临时修正版渲染。"
  fi

  printf '[%02d/%02d] %s ... ' \
    "$((success_count + failure_count + 1))" "${#mmd_files[@]}" "$filename"

  if "$mmdc" \
      -i "$render_input" \
      -o "$output_file" \
      -b white \
      -w "$png_width" \
      -s "$png_scale" \
      -q; then
    echo "OK"
    ((success_count += 1))
  else
    echo "FAILED" >&2
    ((failure_count += 1))
  fi
done

echo
echo "完成：成功 ${success_count}，失败 ${failure_count}。"
echo "PNG 目录：${output_dir}"

if (( failure_count > 0 )); then
  exit 1
fi
