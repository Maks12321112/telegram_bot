from datetime import datetime

import sqlalchemy as sa
import sqlalchemy.orm as orm
from data.sessions import SqlAlchemyBase







class Task(SqlAlchemyBase):
    __tablename__ = 'tasks'
    
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'))
    time = sa.Column(sa.String)
    text = sa.Column(sa.String)
    created_at = sa.Column(sa.DateTime, default=datetime.now)
'''import os
from collections import defaultdict

def get_size(start_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # Пропускаем если это символьная ссылка или недоступный файл
            if not os.path.islink(fp):
                try:
                    total_size += os.path.getsize(fp)
                except (FileNotFoundError, PermissionError):
                    continue
    return total_size

def format_size(size):
    # Преобразуем размер в удобочитаемый формат
    for unit in ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ']:
        if size < 1024:
            return f"{size:.0f}{unit}" if unit == 'Б' else f"{size:.0f}{unit}" if size < 10 else f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}ПБ"

def main():
    path = input("Введите путь: ").strip()
    if not os.path.isdir(path):
        print("Указанный путь не существует или не является каталогом.")
        return
    
    dir_sizes = []
    # Обходим каждый каталог в указанном пути
    for dir_name in os.listdir(path):
        full_dir_path = os.path.join(path, dir_name)
        if os.path.isdir(full_dir_path):
            dir_size = get_size(full_dir_path)
            dir_sizes.append((dir_name, dir_size))
    
    # Сортируем по убыванию размера
    dir_sizes.sort(key=lambda x: -x[1])
    
    # Берем топ 10
    top_dirs = dir_sizes[:10]
    
    # Выводим результат
    for name, size in top_dirs:
        formatted_size = format_size(size)
        # Убираем лишние .0, если они есть
        if '.0' in formatted_size:
            formatted_size = formatted_size.replace('.0', '')
        print(f"{name.ljust(50)} - {formatted_size.rjust(7)}")

if __name__ == "__main__":
    main()'''