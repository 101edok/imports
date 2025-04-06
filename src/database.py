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


def add_video(resource_id, video_data):
    with SessionLocal() as session:
        video = VideoData(
            resource_id=resource_id,
            video_data=video_data,
        )
        session.add(video)
        session.commit()


def is_video_exits(resource_id: str) -> bool:
    with SessionLocal() as session:
        return session.query(exists().where(VideoData.resource_id == resource_id)).scalar()
