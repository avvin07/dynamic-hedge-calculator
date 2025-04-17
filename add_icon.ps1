# Скачиваем Resource Hacker
Write-Host "Downloading Resource Hacker..."
Invoke-WebRequest -Uri "http://www.angusj.com/resourcehacker/resource_hacker.zip" -OutFile "resource_hacker.zip"

# Распаковываем Resource Hacker
Write-Host "Extracting Resource Hacker..."
Expand-Archive -Path "resource_hacker.zip" -DestinationPath "reshacker" -Force

# Создаем копию исполняемого файла
Write-Host "Creating copy of the executable..."
Copy-Item -Path "dist\Калькулятор_Хеджирования_Uniswap_V3.exe" -Destination "dist\hedging_calculator_with_icon.exe" -Force

# Добавляем иконку к EXE-файлу
Write-Host "Adding icon to the EXE file..."
$resourceHackerPath = "reshacker\ResourceHacker.exe"
$exePath = "dist\hedging_calculator_with_icon.exe"
$iconPath = "icon.ico"

Start-Process -FilePath $resourceHackerPath -ArgumentList "-open `"$exePath`" -save `"$exePath`" -action addoverwrite -res `"$iconPath`" -mask ICONGROUP,MAINICON,0" -Wait

Write-Host "Done! The file with icon is: dist\hedging_calculator_with_icon.exe" 