#!/bin/bash

echo ""
echo "###########################"
echo "## Running Deploy Script ##"
echo "###########################"
echo ""

SITE_ROOT_PATH=$1
SERVER_USERNAME=$2
TARGET_BRANCH=$3

set -e # We want to fail at each command, to stop execution.

cd $SITE_ROOT_PATH

# Ensure we are on the correct branch.
if [[ $(git rev-parse --abbrev-ref HEAD) != $TARGET_BRANCH ]] ; then
  git status
  echo "The site is on the incorrect branch. Who did work on directly on $TARGET_BRANCH? Exiting."
  exit 1
fi

echo ""
echo "########################"
echo "## Running GIT Deploy ##"
echo "########################"
echo ""

# Pull down the site files.
git fetch origin
git merge --ff origin/$TARGET_BRANCH

# Deployment done!
echo ""
echo "##########################"
echo "## Deployment complete! ##"
echo "##########################"
echo ""
