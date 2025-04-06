import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from sqlalchemy import Column, String, Integer
from sqlalchemy.sql import exists


Base = declarative_base()


class VideoData(Base):
    __tablename__ = 'video_data'

    resource_id = Column(String(128), primary_key=True, index=True)

    import_id   = Column(Integer, nullable=False)

    video_data  = Column(String, nullable=False)
    llava_data  = Column(String, nullable=True)
    recipe_data = Column(String, nullable=True)


MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
engine = create_engine(f"mysql://recepter:{MYSQL_PASSWORD}@recepter.mysql.gistrec.cloud:3306/recepter", pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def add_video(import_id: int, resource_id: int, video_data: str):
    """
    Добавляет запись о видео в базу данных.
    """
    with SessionLocal() as session:
        video = VideoData(
            import_id=import_id,
            resource_id=resource_id,
            video_data=video_data,
        )
        session.add(video)
        session.commit()


def is_video_exists(resource_id: str) -> bool:
    """
    Проверяет, существует ли видео с заданным resource_id.
    """
    with SessionLocal() as session:
        return session.query(exists().where(VideoData.resource_id == resource_id)).scalar()


def get_videos(import_id: int):
    """
    Возвращает все записи из таблицы video_data.
    """
    with SessionLocal() as session:
        return session.query(VideoData).filter(VideoData.import_id == import_id).all()


def set_llava_data(resource_id, llava_data):
    """
    Обновляет для видео с resource_id поле llava_data.
    """
    with SessionLocal() as session:
        video = session.query(VideoData).filter(VideoData.resource_id == resource_id).one()
        video.llava_data = llava_data
        session.commit()