# Контейнер для импорта видео

## Переменные окружения

* (required) S3_SECRET_KEY
* (required) GOOGLE_API_KEY
* (required) MYSQL_PASSWORD

## Параметры контейнера

* (required) IMPORT_ID
* (required) YOUTUBE_CHANNEL_URL
* (optional) MAX_VIDEO_COUNT (default 10)
* (optional) MAX_VIDEO_DURATION_SEC (default 180)
* (optional) MAX_VIDEO_SIZE_MB (default 20)
* (optional) INGREDIENTS_PROMPT (default ...)
* (optional) TIMECODES_PROMPT (default ...)
* (optional) EQUIPMENTS_PROMPT (default ...)
* (optional) INSTRUCTIONS_PROMPT (default ...)

## Запуск на `RunPod`

```bash
# Пеоед началом работы
service nginx stop

apt update
apt install -y nano

pip install --upgrade pip

# Устанавливаем imports
apt install -y libmysqlclient-dev pkg-config
git clone https://github.com/101edok/imports.git
pip install -r imports/requirements.txt

# Устанавливаем Video-LLaVA
git clone https://github.com/PKU-YuanGroup/Video-LLaVA
pip install -e Video-LLaVA/
pip install -U transformers
python -m pip install av

# TODO: Проверить надо или нет
# pip install flash-attn --no-build-isolation
# pip install decord opencv-python git+https://github.com/facebookresearch/pytorchvideo.git@28fe037d212663c6a24f373b94cc5d478c8c1a1d


# Решает проблему
#
# TypeError: Descriptors cannot be created directly.
# If this call came from a _pb2.py file, your generated code is out of date and must be regenerated with protoc >= 3.19.0.
# If you cannot immediately regenerate your protos, some other possible workarounds are:
#   1. Downgrade the protobuf package to 3.20.x or lower.
#   2. Set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python (but this will use pure-Python parsing and will be much slower).
pip install protobuf==3.20.3

# TODO: Проверить надо или нет
# pip install timm==1.0.13
```
