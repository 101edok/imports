import cv2


def get_video_duration(video_path):
    video = cv2.VideoCapture(video_path)
    return video.get(cv2.CAP_PROP_POS_MSEC) * 1000


def extract_first_frame(video_path, photo_path):
    video = cv2.VideoCapture(video_path)
    success, image = video.read()
    if not success:
        print("Failed to read video " + video_path)
        return

    cv2.imwrite(photo_path, image)
