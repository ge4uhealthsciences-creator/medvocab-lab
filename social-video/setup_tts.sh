#!/usr/bin/env bash
# Downloads the offline Kokoro TTS (sherpa-onnx) used for GE4u video voiceovers.
# Everything comes from GitHub releases, so it works on GitHub Actions and in restricted sandboxes.
set -euo pipefail
DIR="${GE4U_TTS_DIR:-$HOME/ge4u-tts}"
VER="v1.13.8"
mkdir -p "$DIR"
cd "$DIR"
if ! ls sherpa-onnx-*/bin/sherpa-onnx-offline-tts >/dev/null 2>&1; then
  curl -fsSL -o bin.tar.bz2 "https://github.com/k2-fsa/sherpa-onnx/releases/download/${VER}/sherpa-onnx-${VER}-linux-x64-static.tar.bz2"
  tar xjf bin.tar.bz2 && rm bin.tar.bz2
fi
if [ ! -f kokoro-en-v0_19/model.onnx ]; then
  curl -fsSL -o kokoro.tar.bz2 "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-en-v0_19.tar.bz2"
  tar xjf kokoro.tar.bz2 && rm kokoro.tar.bz2
fi
echo "TTS ready in $DIR"
