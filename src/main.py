import os
import re
import json

from pytubefix import YouTube


from s3 import upload_file
from cv import get_video_duration, extract_first_frame
from youtube import get_channel_id, get_videos, get_transcript
from database import add_video, is_video_exits


channel_urls = [
    "https://www.youtube.com/al_dante_channel/shorts",
]

pattern = r'https://www\.youtube\.com/([^/]+)/shorts'


for channel_url in channel_urls:
    channel_name = re.search(pattern, channel_url).group(1)
    channel_id = get_channel_id(channel_name)

    videos = get_videos(channel_id, 50)

    for video in videos:
        resource_id = video["snippet"]["resourceId"]["videoId"]
        video_url = "https://www.youtube.com/watch?v=" + resource_id

        if is_video_exits(resource_id=resource_id):
            print(f"Video {video['id']} has been already uploaded")
            continue

        transcript = get_transcript(video)
        if not transcript:
            print(f"Failed to get transcript for video {video_url}")

        video_folder = "/content/videos/"
        video_name   = resource_id + ".mp4"
        preview_name = resource_id + ".jpg"

        video_path = video_folder + video_name
        preview_path = video_folder + preview_name

        try:
            yt = YouTube(video_url)

            mp4_streams = yt.streams.filter(file_extension='mp4')
            mp4_stream = mp4_streams[0]

            mp4_stream.download(output_path=video_folder, filename=video_name)
        except Exception as e:
            print(f"Failed to download video {video_url}: ", e)
            continue

        duration_sec = get_video_duration(video_path)
        if duration_sec > 180:
            print(f"Video {video_url} is too long - {duration_sec} sec")
            continue

        video_syze_bytes = os.path.getsize(video_path)
        if video_syze_bytes > 1024 * 1024 * 20:
            print(f"Video {video_url} is too big: " + str(round(video_syze_bytes / 1024 / 1024, 2)) + " MB")

        extract_first_frame(video_path, preview_path)

        video_s3_key = "mined_videos/" + video_name
        preview_s3_key = "mined_videos/" + preview_name

        try:
            basket = "recepter"

            upload_file(video_path, basket, video_s3_key)
            upload_file(preview_path, basket, preview_s3_key)
        except:
            print(f"Failed to upload video {video_url} to S3")

        data_str = json.dumps({
            "id": video["id"],

            "video_syze_bytes": video_syze_bytes,

            "video_s3_key": video_s3_key,
            "preview_s3_key": preview_s3_key,

            "url": video_url,
            "resource_id": resource_id,

            "channel_id": channel_id,
            "channel_name": channel_name,

            "diration_sec": duration_sec,
            "published_at": video["snippet"]["publishedAt"],

            "title": video["snippet"]["title"],
            "description": video["snippet"]["description"],

            "transcript": transcript,

            "thumbnails": video["snippet"]["thumbnails"],
        }, ensure_ascii=False)

        add_video(resource_id, data_str)

        print(f"Video {video_url} uploaded")
