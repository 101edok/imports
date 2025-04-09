import os

from googleapiclient.discovery import build

from youtube_transcript_api import YouTubeTranscriptApi


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
youtube = build('youtube', 'v3', developerKey=GOOGLE_API_KEY)


# Search for the channel by username or custom URL
def get_channel_id(channel_username: str) -> str:
    response = youtube.search().list(
        part='snippet',
        q=channel_username,
        type='channel'
    ).execute()

    # Extract the channel ID
    if response['items']:
        return response['items'][0]['snippet']['channelId']

    return None


def get_videos(channel_id: str, limit: int = 100) -> list:
    # Get the playlist ID for the channel's uploads
    response = youtube.channels().list(
        part='contentDetails',
        id=channel_id
    ).execute()

    uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    # Get the videos from the uploads playlist
    videos = []
    next_page_token = None

    while True:
        # 50 - лимит на количество видео в одном запросе
        maxResults = min(limit, 50 - len(videos))

        response = youtube.playlistItems().list(
            part='snippet,contentDetails',
            playlistId=uploads_playlist_id,
            maxResults=maxResults,
            pageToken=next_page_token
        ).execute()

        if len(response['items']) == 0:
            break

        videos.extend(response['items'])

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

        if len(videos) >= limit:
            break

    return videos


def get_transcript(video) -> str:
    resource_id = video["snippet"]["resourceId"]["videoId"]

    try:
        transcript_dict = YouTubeTranscriptApi.get_transcript(resource_id, languages=["ru"])
        final_transcript = " ".join(i["text"] for i in transcript_dict)

        return final_transcript
    except:
        return None
