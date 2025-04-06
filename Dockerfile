FROM pytorch/pytorch:latest

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл зависимостей (если он у вас есть)
COPY requirements.txt ./

# Устанавливаем системные зависимости
RUN apt-get update
RUN apt-get install -y libmysqlclient-dev pkg-config gcc libgl1-mesa-glx


# Обновляем pip и устанавливаем зависимости
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Копируем все файлы из текущей директории в контейнер
COPY src/. .

# Определяем команду, которая будет запускаться при старте контейнера
# Замените "main.py" на название вашего основного Python файла
CMD ["python", "main.py"]
