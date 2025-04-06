import cv2
import logging


def get_video_duration(video_path):
    """
    Возвращает длительность видео (в секундах) на основе количества кадров и FPS.
    """
    cap = cv2.VideoCapture(video_path)
    assert cap.isOpened(), f"Не удалось открыть видео: {video_path}"

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    cap.release()

    return frame_count / fps if fps else 0


def extract_first_frame(video_path, photo_path):
    """
    Извлекает первый кадр из видео и сохраняет его по указанному пути.
    """
    cap = cv2.VideoCapture(video_path)
    success, image = cap.read()
    assert success, f"Не удалось прочитать первый кадр из видео: {video_path}"

    cv2.imwrite(photo_path, image)
    cap.release()
