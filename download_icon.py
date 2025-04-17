import requests
import os

# URL к готовой иконке графика
url = "https://icons.iconarchive.com/icons/paomedia/small-n-flat/256/analytics-icon.ico"

# Получаем иконку
response = requests.get(url)

# Сохраняем файл
with open("icon.ico", "wb") as file:
    file.write(response.content)

print("Иконка успешно загружена и сохранена как icon.ico") 