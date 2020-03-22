#!/usr/bin/python3
"""あさココの配信予定枠を検索する"""
import datetime
import os
import subprocess
from time import sleep

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from const import *

EXEC_PATH = 'python3 /home/mekabu/asacoco_caster/'
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)

def search_videos():
  """あさココの検索結果から配信予定枠を検索して動画IDを返す"""
  search_response = youtube.search().list(
    q='あさココ',
    part='snippet',
    channelId='UCS9uQI-jC3DE0L4IpXyvr6w',
    maxResults=5
  ).execute()

  video_id = None

  for search_result in search_response.get('items', []):
    if search_result['id']['kind'] == 'youtube#video':
      if search_result['snippet']['liveBroadcastContent'] == 'upcoming':
        # 配信予定枠が見つかったらvideoIdを取得する
        video_id = search_result['id']['videoId']
        break

  return video_id


def get_scheduledtime(video_id):
  """配信予定枠の動画IDから配信開始予定時間を取得しての5分前の時刻をatコマンドのフォーマットで返す"""
  videos_response = youtube.videos().list(
    part='liveStreamingDetails',
    id=video_id
  ).execute()

  for search_result in videos_response.get('items', []):
    scheduled = datetime.datetime.strptime(search_result['liveStreamingDetails']['scheduledStartTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
    scheduled_jst = scheduled + datetime.timedelta(hours=8, minutes=55)

  return scheduled_jst.strftime('%H:%M %m%d%Y')


if __name__ == '__main__':

  try:
    video_id = search_videos()
    if video_id:
      # 配信開始予定時間を取得して5分前に監視スクリプトを起動予約する
      start_time = get_scheduledtime(video_id)
      p = subprocess.Popen(['at', start_time], stdin=subprocess.PIPE)
      command = '%slivestate.py -i %s' % (EXEC_PATH, video_id)
      p.communicate(command.encode('utf-8'))
    else:
      # 配信予定枠が見つからなかったら1時間後に再検索する(5時以降はしない)
      nowtime = datetime.datetime.strptime(((datetime.datetime.now()+datetime.timedelta(hours=1)).strftime('%H:%M:%S')), '%H:%M:%S')
      threstime = datetime.datetime.strptime('05:00:00', '%H:%M:%S')
      if nowtime < threstime:
        p = subprocess.Popen(['at', 'now + 1hours'], stdin=subprocess.PIPE)
        command = '%sbooking.py' % EXEC_PATH
        p.communicate(command.encode('utf-8'))
  except HttpError as e:
    print('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))
