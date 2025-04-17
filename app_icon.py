from PIL import Image
import io
import os

# Создаем папку для иконки, если ее нет
if not os.path.exists('icons'):
    os.makedirs('icons')

# Создаем пустое изображение с прозрачным фоном (без черной рамки)
img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))

# Создаем зеленый фон с закругленными краями
background = Image.new('RGBA', (240, 240), (40, 167, 69, 255))
# Добавляем желтые столбики
for i in range(4):
    bar_height = 40 + i * 20
    bar = Image.new('RGBA', (40, bar_height), (255, 193, 7, 255))
    background.paste(bar, (40 + i * 50, 240 - bar_height), bar)

# Добавляем стрелку
# (упрощенная версия)

# Сохраняем как иконку
background.save('icons/app_icon.ico', format='ICO')

print("Иконка создана и сохранена в файл icons/app_icon.ico") 