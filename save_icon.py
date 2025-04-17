from PIL import Image
import io
import os
import sys
import tkinter as tk
from tkinter import filedialog

# Создаем временный корневой объект tkinter для диалога
root = tk.Tk()
root.withdraw()  # Скрываем основное окно

print("Сохранение иконки для приложения...")

# Определяем путь к текущей директории
current_dir = os.getcwd()

# Предлагаем выбрать файл изображения
file_path = filedialog.askopenfilename(
    title="Выберите изображение для иконки",
    filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp")],
    initialdir=current_dir
)

if not file_path:
    print("Файл не выбран. Операция отменена.")
    sys.exit(0)

try:
    # Открываем исходное изображение
    img = Image.open(file_path)
    
    # Создаем иконки разных размеров
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    
    # Путь для сохранения .ico файла
    icon_path = os.path.join(current_dir, "app_icon.ico")
    
    # Преобразуем и сохраняем как .ico
    img.save(icon_path, format="ICO", sizes=icon_sizes)
    
    print(f"Иконка успешно сохранена: {icon_path}")
    
except Exception as e:
    print(f"Ошибка при сохранении иконки: {e}") 