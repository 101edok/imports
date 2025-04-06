# Контейнер для импорта видео

## Переменные окружения

* S3_SECRET_KEY
* GOOGLE_API_KEY
* MYSQL_PASSWORD

## Параметры контейнера

* (required) IMPORT_ID
* (required) YOUTUBE_CHANNEL_URL
* (optional) MAX_VIDEO_DURATION_SEC (default 180)
* (optional) MAX_VIDEO_SIZE_MB (default 20)
* (optional) INGREDIENTS_PROMPT (default ...)
* (optional) TIMECODES_PROMPT (default ...)
* (optional) EQUIPMENTS_PROMPT (default ...)
* (optional) INSTRUCTIONS_PROMPT (default ...)
