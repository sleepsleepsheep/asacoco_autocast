#!/usr/bin/python3
"""配信状態を監視して、配信中ならChromecastへキャストする"""
import argparse
from time import sleep

import pychromecast
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pychromecast.controllers.youtube import YouTubeController

from const import *

_CAST_DEV_NAME = 'テレビ'

def youtube_livestate(video_id):
  """指定した動画の配信状態を返す"""
  if not video_id or len(video_id) != 11:
    exit()

  youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
  videos_response = youtube.videos().list(
    part='snippet',
    id=video_id
  ).execute()

  for search_result in videos_response.get('items', []):
      result = search_result['snippet']['liveBroadcastContent']

  return result


def cast_device(video_id):
  """指定した動画IDの動画をデバイスにキャストする"""
  chromecasts = pychromecast.get_chromecasts()

  cast = next(cc for cc in chromecasts if cc.device.friendly_name == _CAST_DEV_NAME)
  cast.wait()

  yt = YouTubeController()
  cast.register_handler(yt)
  yt.play_video(video_id)


if __name__ == '__main__':

  parser = argparse.ArgumentParser()
  parser.add_argument('-i', help='video_id', default=None)
  args = parser.parse_args()

  try:
    for dummy in range(70):
      # 配信中でない場合30秒待ってリトライする。
      # リトライ回数は最大70回(70x30=2100sec=35min)
      if youtube_livestate(args.i) == 'live':
        cast_device(args.i)
        break
      sleep(30)
  except HttpError as e:
    print('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))
