#!/usr/bin/env bash
# Regenerates the committed test videos. Needs ffmpeg (with libx264, libx265,
# libvpx-vp9) on the PATH. The generated files are committed, so running the
# tests does NOT need ffmpeg. Every file stays far below the 5 MB repo limit.
#
# Frame marker: in the reference videos, source frame n (counted from 0)
# shows a white rectangle whose left edge is at x = X0 + 8*(n+1): ffmpeg counts
# the overlay variable n from 1 here (REF-A: 108, 116, ...). Tests use it
# to tell exactly which frame they were given.
set -euo pipefail
cd "$(dirname "$0")"
FF="ffmpeg -v error -y"
BG=0x202428

marker() { # size fps x0 y w h frames out [extra output options...]
  local size=$1 fps=$2 x0=$3 y=$4 w=$5 h=$6 frames=$7 out=$8; shift 8
  $FF -f lavfi -i "color=c=$BG:s=$size:r=$fps" -f lavfi -i "color=c=white:s=${w}x${h}:r=$fps" \
      -filter_complex "[0][1]overlay=x=$x0+8*n:y=$y" -frames:v "$frames" \
      -c:v libx264 -pix_fmt yuv420p "$@" "$out"
}
plain() { # size fps frames out [extra output options...]
  local size=$1 fps=$2 frames=$3 out=$4; shift 4
  $FF -f lavfi -i "color=c=$BG:s=$size:r=$fps" -frames:v "$frames" -c:v libx264 -pix_fmt yuv420p "$@" "$out"
}

# --- reference videos -------------------------------------------------------
marker 1280x720 30 100 300 80 50 90 ref_720p.mp4                       # REF-A
marker 640x360  25 40  150 40 30 50 ref_360p.mp4                       # REF-B
plain  1280x720 30 18000 long_720p_10min.mp4 -preset veryfast          # REF-D

# REF-C / performance video: 30 s, a textured target moving on a static noisy
# background. Target centre: cx = 640 + 300*sin(2*pi*n/450),
#                            cy = 360 + 150*sin(2*pi*n/300); size 96 x 64.
$FF -f lavfi -i "nullsrc=s=1280x720,geq=lum='96+32*random(1)':cb=128:cr=128" -frames:v 1 _bg.png
$FF -loop 1 -framerate 30 -i _bg.png -f lavfi -i "testsrc2=s=96x64:r=30" \
    -filter_complex "[0][1]overlay=x='640+300*sin(2*PI*n/450)-48':y='360+150*sin(2*PI*n/300)-32'" \
    -frames:v 900 -c:v libx264 -preset medium -crf 30 -pix_fmt yuv420p bench_720p_30s.mp4
rm -f _bg.png

# REF-V: variable frame rate. Source ticks n with n mod 3 == 1 are dropped,
# so frames alternately last 2 ticks (1/15 s) and 1 tick (1/30 s): 60 frames, 3.0 s.
$FF -f lavfi -i "color=c=$BG:s=1280x720:r=30" -f lavfi -i "color=c=white:s=80x50:r=30" \
    -filter_complex "[0][1]overlay=x=100+8*n:y=300,select='not(eq(mod(n\,3)\,1))'" \
    -frames:v 60 -fps_mode vfr -c:v libx264 -pix_fmt yuv420p vfr_720p.mp4

# 29.97 fps
marker 1280x720 30000/1001 100 300 80 50 90 ntsc_720p.mp4

# --- damaged files ----------------------------------------------------------
marker 1280x720 30 100 300 80 50 90 _ref_fs.mp4 -movflags +faststart
python3 - <<'EOF'
data = open("_ref_fs.mp4", "rb").read()
i = data.find(b"mdat")                       # index (moov) comes first, picture data after it
open("damaged_720p.mp4", "wb").write(data[: i + (len(data) - i) // 2])   # REF-X: index intact, data cut
plain = open("ref_720p.mp4", "rb").read()    # moov at the end: cutting the end removes the index
open("truncated.mp4", "wb").write(plain[: len(plain) // 2])
EOF

# --- other containers and codecs -------------------------------------------
SRC="color=c=$BG:s=320x180:r=25"
$FF -f lavfi -i "$SRC" -frames:v 10 -c:v mpeg4 clip.avi
$FF -f lavfi -i "$SRC" -frames:v 10 -c:v libx264 -pix_fmt yuv420p clip.mkv
$FF -f lavfi -i "$SRC" -frames:v 10 -c:v libvpx-vp9 clip.webm
$FF -f lavfi -i "$SRC" -frames:v 10 -c:v libx265 -pix_fmt yuv420p -tag:v hvc1 -x265-params log-level=error clip_hevc.mp4
$FF -f lavfi -i "$SRC" -frames:v 10 -c:v mpeg4 clip_mpeg4.mp4
$FF -f lavfi -i "sine=frequency=440:duration=1" -c:a aac audio_only.mp4
$FF -f lavfi -i "$SRC" -frames:v 10 -c:v libx264 -pix_fmt yuv420p -f mov phone.mov
$FF -f lavfi -i "$SRC" -frames:v 10 -c:v libx265 -pix_fmt yuv420p -tag:v hvc1 -x265-params log-level=error -f mov phone_hevc.mov
$FF -f lavfi -i "$SRC" -frames:v 10 -c:v libx264 -pix_fmt yuv420p -f 3gp old_phone.3gp
$FF -f lavfi -i "color=c=$BG:s=176x144:r=25" -frames:v 10 -c:v h263 old_phone_h263.3gp

# --- colour formats ---------------------------------------------------------
$FF -f lavfi -i "$SRC" -frames:v 10 -c:v libx264 -pix_fmt yuvj420p    h264_fullrange.mp4
$FF -f lavfi -i "$SRC" -frames:v 10 -c:v libx264 -pix_fmt yuv420p10le h264_10bit.mp4
$FF -f lavfi -i "$SRC" -frames:v 10 -c:v libx264 -pix_fmt yuv422p     h264_422.mp4
$FF -f lavfi -i "$SRC" -frames:v 10 -c:v libx264 -pix_fmt yuv444p     h264_444.mp4

# --- extra tracks (all based on REF-A) --------------------------------------
A=_ref_fs.mp4
$FF -i $A -f lavfi -i "sine=frequency=440:duration=4" -map 0:v -map 1:a -c:v copy -c:a aac with_sound.mp4
$FF -i $A -map 0:v -c copy -timecode 00:00:00:00 with_data.mp4
$FF -i $A -f lavfi -i "sine=frequency=440:duration=4" -map 0:v -map 1:a -c:v copy -c:a aac -timecode 00:00:00:00 with_sound_data.mp4
$FF -i $A -i ref_360p.mp4 -map 0:v -map 1:v -c copy two_videos.mp4
$FF -f lavfi -i "color=c=gray:s=160x90" -frames:v 1 _thumb.jpg
$FF -i $A -i _thumb.jpg -map 0:v -map 1:v -c:v:0 copy -c:v:1 mjpeg with_preview.mp4
$FF -i $A -i _thumb.jpg -map 0:v -map 1:v -c:v:0 copy -c:v:1 mjpeg -disposition:v:1 attached_pic with_cover_tag.mp4

# --- picture sizes (3 frames each) ------------------------------------------
for wh in 1278x720 1280x718 722x720 1282x720 1280x722 1920x1080 32x18 360x640 718x720 \
          720x720 960x960 1440x480 1600x576 962x962 1602x576; do
  plain $wh 30 3 res_$wh.mp4
done

# --- lengths ----------------------------------------------------------------
plain 1280x720 30 1 one_frame.mp4
plain 1280x720 30 2 two_frames.mp4
plain 1280x720 30 3 three_frames.mp4

# --- rotation notes ---------------------------------------------------------
for a in 90 180 270; do $FF -display_rotation $a -i $A -c copy rot_$a.mp4; done
plain 1920x1080 30 1 _tp.mp4
$FF -display_rotation 180 -i _tp.mp4 -c copy three_problems.mp4

rm -f _ref_fs.mp4 _thumb.jpg _tp.mp4
echo "fixtures: $(ls | grep -vc generate_fixtures.sh) files, largest: $(ls -S | head -1) ($(du -k "$(ls -S | head -1)" | cut -f1) kB), total $(du -sk . | cut -f1) kB"
