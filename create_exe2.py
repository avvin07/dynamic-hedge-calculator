import os
import subprocess
import shutil

# Путь для существующей иконки
icon_path = "icon.ico"

# Функция для создания spec-файла
def create_spec_file():
    print("Создаем spec-файл...")
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['uniswap_v3_hedge_calculator.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['numpy', 'matplotlib', 'pandas', 'tkinter'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='hedge_calculator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='""" + icon_path + """',
)
"""
    with open("hedge_calculator2.spec", "w") as file:
        file.write(spec_content)
    print("Spec-файл создан: hedge_calculator2.spec")

# Функция для сборки EXE-файла
def build_exe():
    print("Собираем EXE-файл...")
    try:
        # Удаляем старые файлы сборки, если они существуют
        if os.path.exists("build/hedge_calculator"):
            shutil.rmtree("build/hedge_calculator")
        if os.path.exists("dist/hedge_calculator.exe"):
            os.remove("dist/hedge_calculator.exe")
        
        # Запускаем PyInstaller
        subprocess.run(["pyinstaller", "hedge_calculator2.spec"], check=True)
        print("EXE-файл успешно создан: dist/hedge_calculator.exe")
        return True
    except Exception as e:
        print(f"Ошибка при сборке EXE-файла: {e}")
        return False

# Основная функция
def main():
    print("Запускаем процесс создания EXE-файла с иконкой...")
    
    # Проверяем наличие иконки
    if not os.path.exists(icon_path):
        print(f"Ошибка: иконка {icon_path} не найдена!")
        return
    
    # Создаем spec-файл
    create_spec_file()
    
    # Собираем EXE-файл
    success = build_exe()
    
    if success:
        print("Процесс завершен успешно!")
        print("EXE-файл с иконкой находится в папке dist/hedge_calculator.exe")
    else:
        print("Не удалось создать EXE-файл с иконкой.")

if __name__ == "__main__":
    main() 