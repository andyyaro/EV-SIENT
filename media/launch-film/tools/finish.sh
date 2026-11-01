#!/bin/bash
# Finish the 60 fps render into the film: each pair of frames blends into one 30 fps frame (the motion blur of a
# half-frame shutter), then one grade (a gentle S-curve, slightly cool shadows), a soft vignette and fine luma
# grain; the mix is muxed in. -> renders/ev-sient-launch-v2.mp4, plus the poster for the watch page.
set -euo pipefail
cd "$(dirname "$0")/.."
IN=${1:-renders/v2-raw60.mp4}
OUT=${2:-renders/ev-sient-launch-v2.mp4}
VF="tmix=frames=2:weights='1 1',select='eq(mod(n\,2)\,1)',setpts=N/(30*TB),fps=30"
VF="$VF,curves=master='0/0 0.06/0.048 0.5/0.5 0.94/0.952 1/1'"
VF="$VF,colorbalance=rs=-0.012:bs=0.022:rh=0.006:bh=-0.004,eq=saturation=1.04"
VF="$VF,vignette=angle=0.36:mode=forward"
VF="$VF,noise=c0s=3:c0f=t+u,format=yuv420p"
ffmpeg -v error -stats -y -i "$IN" -i assets/audio/mix.wav -map 0:v:0 -map 1:a:0 -vf "$VF" \
  -c:v libx264 -preset slow -crf 17 -profile:v high -pix_fmt yuv420p -c:a aac -b:a 256k -ar 48000 \
  -movflags +faststart -t 59 "$OUT"
mkdir -p deploy/film
ffmpeg -v error -y -ss 4.9 -i "$OUT" -frames:v 1 -q:v 3 deploy/film/poster.jpg
echo "wrote $OUT and deploy/film/poster.jpg"
