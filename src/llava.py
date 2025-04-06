import os
import time
import json
import re
import logging
import av
import numpy as np

from transformers import VideoLlavaProcessor, VideoLlavaForConditionalGeneration

from s3 import download_s3_file
from database import get_videos, set_llava_data


# Папка для временного сохранения видео
VIDEO_FOLDER = "./videos"
os.makedirs(VIDEO_FOLDER, exist_ok=True)



# Определяем промпты для анализа
INGREDIENTS_PROMPT  = os.getenv("INGREDIENTS_PROMPT",  "USER: <video>List all the ingredients used in the dish shown in this video. Include quantities if mentioned. ASSISTANT:")
TIMECODES_PROMPT    = os.getenv("TIMECODES_PROMPT",    "USER: <video>Provide the timecodes for each significant step in the cooking process shown in this video. ASSISTANT:")
EQUIPMENTS_PROMPT   = os.getenv("EQUIPMENTS_PROMPT",   "USER: <video>List all the specific kitchen equipment used in the cooking process shown in this video. ASSISTANT:")
INSTRUCTIONS_PROMPT = os.getenv("INSTRUCTIONS_PROMPT", "USER: <video>Provide a detailed step-by-step guide for the cooking process shown in this video. Make sure the instructions are clear and concise. ASSISTANT:")

# Загружаем модель и процессор Video LLaVA (убедитесь, что на GPU достаточно видеопамяти)
model = VideoLlavaForConditionalGeneration.from_pretrained("LanguageBind/Video-LLaVA-7B-hf").to("cuda")
processor = VideoLlavaProcessor.from_pretrained("LanguageBind/Video-LLaVA-7B-hf")


def read_video_pyav(container, indices):
    """
    Извлекает кадры из видео с использованием PyAV по заданным индексам.
    """
    frames = []
    container.seek(0)
    start_index = indices[0]
    end_index = indices[-1]
    for i, frame in enumerate(container.decode(video=0)):
        if i > end_index:
            break
        if i >= start_index and i in indices:
            frames.append(frame)
    return np.stack([x.to_ndarray(format="rgb24") for x in frames])


def process_video_llava(video_path, prompt, model, processor):
    """
    Обрабатывает видео с помощью Video LLaVA.
    """
    try:
        container = av.open(video_path)
    except Exception as e:
        logging.error(f"Ошибка открытия видео {video_path}: {e}")
        return None

    if not container.streams.video:
        logging.error(f"В видео {video_path} отсутствует видеопоток")
        return None

    total_frames = container.streams.video[0].frames
    if total_frames <= 0:
        logging.error(f"Видео {video_path} не содержит кадров")
        return None

    indices = np.arange(0, total_frames, total_frames / 8).astype(int)
    clip = read_video_pyav(container, indices)
    inputs = processor(text=prompt, videos=clip, return_tensors="pt").to("cuda")
    generate_ids = model.generate(**inputs, max_length=1024, do_sample=True, temperature=0.7, top_p=0.9)
    result = processor.batch_decode(generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
    return result


def clean_recipe_response(response):
    """
    Очищает ответ от лишних пробелов и нежелательных фрагментов.
    """
    response = re.sub(r'\s+', ' ', response).strip()
    response = re.sub(r'USER:.*ASSISTANT: ', '', response)
    return response


def process_videos_with_llava(import_id: int):
    """
    Основная функция обработки видео с помощью Video LLaVA.
    Для каждого видео из базы (у которого не заполнено llava_data):
      - загружается видео из S3,
      - запускается обработка с несколькими промптами,
      - результат сохраняется в базе.
    """
    videos = get_videos(import_id)
    for video in videos:
        resource_id = video.resource_id

        if video.llava_data is not None:
            logging.info(f"Видео {resource_id} уже обработано – пропускаем")
            continue

        video_info = json.loads(video.video_data)

        video_path = os.path.join(VIDEO_FOLDER, resource_id + ".mp4")
        start_time = time.time()

        if not os.path.exists(video_path):
            logging.info(f"Видео {resource_id} не найдено локально – скачиваем")
            if not download_s3_file(video_info["video_s3_key"], video_path):
                logging.error(f"Ошибка скачивания видео {resource_id} из S3")
                continue

        try:
            ingredients_result  = process_video_llava(video_path, INGREDIENTS_PROMPT,  model, processor)
            timecodes_result    = process_video_llava(video_path, TIMECODES_PROMPT,    model, processor)
            equipments_result   = process_video_llava(video_path, EQUIPMENTS_PROMPT,   model, processor)
            instructions_result = process_video_llava(video_path, INSTRUCTIONS_PROMPT, model, processor)

            llava_result = {
                "ingredients":  clean_recipe_response(ingredients_result)  if ingredients_result  else "",
                "timecodes":    clean_recipe_response(timecodes_result)    if timecodes_result    else "",
                "equipments":   clean_recipe_response(equipments_result)   if equipments_result   else "",
                "instructions": clean_recipe_response(instructions_result) if instructions_result else "",
            }
            llava_data = json.dumps(llava_result, ensure_ascii=False)
            set_llava_data(resource_id, llava_data)
            logging.info(f"Видео {resource_id} обработано: {llava_data}")
        except Exception as e:
            logging.error(f"Ошибка при обработке Video LLaVA для {resource_id}: {e}")

        elapsed_time = time.time() - start_time
        logging.info(f"Время обработки видео {resource_id}: {elapsed_time:.2f} сек")
