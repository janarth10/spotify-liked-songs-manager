#!/bin/bash


echo "starting spotify cron"
cd /Users/newdev/Hive/Development/personal_projects/spotify-liked-songs-manager/

sleep 5

source venv/bin/activate

sleep 5

python3 app.py

now=$(date)
echo "Spotify Cron last run at $now"