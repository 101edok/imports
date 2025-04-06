import os
import re
import json
import logging

from pytubefix import YouTube

from s3 import upload_file
from cv import get_video_duration, extract_first_frame
from youtube import get_channel_id, get_videos, get_transcript
from database import add_video, is_video_exists


# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


VIDEO_FOLDER = "./videos"
S3_BASKET = "recepter"

# Получаем параметры из переменных окружения или используем значения по умолчанию
MAX_VIDEO_DURATION_SEC = int(os.getenv("MAX_VIDEO_DURATION_SEC", 180))
MAX_VIDEO_SIZE_MB = int(os.getenv("MAX_VIDEO_SIZE_MB", 20))
YOUTUBE_CHANNEL_URL = os.getenv("YOUTUBE_CHANNEL_URL", "https://www.youtube.com/your_channel/shorts")

YOUTUBE_SHORTS_PATTERN = r'https://www\.youtube\.com/([^/]+)/shorts'


def process_video(video, channel_id, channel_name):
    """
    Обрабатывает одно видео:
    - Проверяет, не было ли видео уже загружено
    - Скачивает видео и извлекает превью
    - Проводит валидацию длительности и размера видео
    - Загружает файлы на S3
    - Сохраняет информацию о видео в базу данных
    """
    resource_id = video["snippet"]["resourceId"]["videoId"]
    video_url = f"https://www.youtube.com/watch?v={resource_id}"

    if is_video_exists(resource_id=resource_id):
        logging.info(f"Видео {video['id']} уже загружено")
        return

    transcript = get_transcript(video)
    if not transcript:
        logging.warning(f"Не удалось получить транскрипт для {video_url}")

    video_name = f"{resource_id}.mp4"
    preview_name = f"{resource_id}.jpg"
    video_path = os.path.join(VIDEO_FOLDER, video_name)
    preview_path = os.path.join(VIDEO_FOLDER, preview_name)

    # Скачивание видео
    try:
        yt = YouTube(video_url)
        mp4_streams = yt.streams.filter(file_extension='mp4')
        if not mp4_streams:
            logging.error(f"Нет доступных mp4 потоков для {video_url}")
            return
        mp4_stream = mp4_streams[0]
        mp4_stream.download(output_path=VIDEO_FOLDER, filename=video_name)
    except Exception as e:
        logging.error(f"Ошибка скачивания {video_url}: {e}")
        return

    # Проверка длительности видео
    duration_sec = get_video_duration(video_path)
    if duration_sec > MAX_VIDEO_DURATION_SEC:
        logging.info(f"Видео {video_url} слишком длинное - {duration_sec} сек")
        return

    # Проверка размера видео
    video_size_bytes = os.path.getsize(video_path)
    if video_size_bytes > MAX_VIDEO_SIZE_MB * 1024 * 1024:
        size_mb = round(video_size_bytes / (1024 * 1024), 2)
        logging.info(f"Видео {video_url} слишком большое: {size_mb} MB")
        # При необходимости можно завершить обработку здесь

    # Извлечение первого кадра для превью
    extract_first_frame(video_path, preview_path)

    video_s3_key = os.path.join("mined_videos", video_name)
    preview_s3_key = os.path.join("mined_videos", preview_name)

    # Загрузка файлов на S3
    try:
        upload_file(video_path, S3_BASKET, video_s3_key)
        upload_file(preview_path, S3_BASKET, preview_s3_key)
    except Exception as e:
        logging.error(f"Ошибка загрузки {video_url} на S3: {e}")
        return

    # Подготовка данных для записи в базу
    video_data = {
        "id": video["id"],
        "video_size_bytes": video_size_bytes,
        "video_s3_key": video_s3_key,
        "preview_s3_key": preview_s3_key,
        "url": video_url,
        "resource_id": resource_id,
        "channel_id": channel_id,
        "channel_name": channel_name,
        "duration_sec": duration_sec,
        "published_at": video["snippet"]["publishedAt"],
        "title": video["snippet"]["title"],
        "description": video["snippet"]["description"],
        "transcript": transcript,
        "thumbnails": video["snippet"]["thumbnails"],
    }
    data_str = json.dumps(video_data, ensure_ascii=False)
    add_video(resource_id, data_str)
    logging.info(f"Видео {video_url} успешно загружено")


def process_channel(channel_url):
    """
    Обрабатывает все видео канала:
    - Извлекает название канала из URL
    - Получает идентификатор канала и список видео
    - Запускает обработку каждого видео
    """
    match = re.search(YOUTUBE_SHORTS_PATTERN, channel_url)
    if not match:
        logging.error(f"Неверный формат URL канала: {channel_url}")
        return
    channel_name = match.group(1)
    channel_id = get_channel_id(channel_name)
    videos = get_videos(channel_id, 50)
    for video in videos:
        process_video(video, channel_id, channel_name)


def main():
    """
    Главная функция запуска обработки видео с канала.
    """
    os.makedirs(VIDEO_FOLDER, exist_ok=True)
    process_channel(YOUTUBE_CHANNEL_URL)


if __name__ == "__main__":
    main()
