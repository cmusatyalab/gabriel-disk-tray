#!/usr/bin/env bash -e
# Download asset files

die() {
  echo >&2 $*
  exit 1
}

checkCmd() {
  command -v $1 >/dev/null 2>&1 \
    || die "'$1' command not found. Please install from your package manager."
}

checkCmd wget
checkCmd readlink

if ! readlink -e feedbacks && ! readlink -e model; then
  printf "\n====================================================\n"
  printf "Downloading trained DiskTray model and feedback media files.\n"
  printf "They are copyright Carnegie Mellon University and are licensed under\n"
  printf "the Apache 2.0 License.\n\n"
  printf "This will incur about 340MB of network traffic\n"
  printf "====================================================\n\n"
  wget -nv \
    https://storage.cmusatyalab.org/gabriel-model/disktray \
    -O asset.tgz
  [ $? -eq 0 ] || die "+ Error in wget."
  printf "Decompressing downloaded file into model/ and feedbacks/\n"
  tar zxvf asset.tgz
  [ $? -eq 0 ] || die "+ Error decompressing"
else
  printf "'feedbacks' or 'model' directories/files exist. Stopped download to avoid overwriting them.\n"
fi
