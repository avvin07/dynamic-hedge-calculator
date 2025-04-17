import subprocess
import sys
import os
import webbrowser

# Функция для выполнения команд Git
def run_git_command(command):
    try:
        result = subprocess.run(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            shell=True, 
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print(f"Предупреждение/ошибка: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Ошибка при выполнении команды: {e}")
        return False

def main():
    print("===== Помощник загрузки на GitHub =====")
    print("1. Сначала вам нужно создать репозиторий на GitHub")
    print("   (Если вы еще не создали его)")
    
    open_github = input("Открыть GitHub.com для создания репозитория? (y/n): ")
    if open_github.lower() in ['y', 'yes', 'да']:
        webbrowser.open("https://github.com/new")
        print("Пожалуйста, создайте новый репозиторий на GitHub.")
        print("ВАЖНО: Не инициализируйте репозиторий с README, .gitignore или LICENSE.")
        input("Нажмите Enter, когда создадите репозиторий...")
    
    # Запрос URL репозитория
    repo_url = input("Введите URL вашего GitHub репозитория (например, https://github.com/username/repo.git): ")
    if not repo_url:
        print("URL репозитория не указан. Операция отменена.")
        return
    
    # Создание ветки main (если не существует)
    current_branch = subprocess.run(
        "git branch --show-current",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        text=True
    ).stdout.strip()
    
    if not current_branch:
        print("Создание ветки main...")
        run_git_command("git checkout -b main")
    elif current_branch != "main":
        switch_branch = input(f"Текущая ветка: {current_branch}. Переключиться на ветку main? (y/n): ")
        if switch_branch.lower() in ['y', 'yes', 'да']:
            if not run_git_command("git branch -M main"):
                print("Не удалось переименовать/создать ветку main.")
                return
    
    # Добавление удаленного репозитория
    print(f"Добавление удаленного репозитория {repo_url}...")
    
    # Проверка наличия удаленного репозитория
    remote_exists = subprocess.run(
        "git remote -v",
        stdout=subprocess.PIPE,
        shell=True,
        text=True
    ).stdout
    
    if "origin" in remote_exists:
        update_remote = input("Удаленный репозиторий 'origin' уже существует. Обновить его? (y/n): ")
        if update_remote.lower() in ['y', 'yes', 'да']:
            if not run_git_command(f"git remote set-url origin {repo_url}"):
                print("Не удалось обновить удаленный репозиторий.")
                return
        else:
            print("Операция отменена пользователем.")
            return
    else:
        if not run_git_command(f"git remote add origin {repo_url}"):
            print("Не удалось добавить удаленный репозиторий.")
            return
    
    # Отправка коммитов на GitHub
    print("Отправка коммитов на GitHub...")
    if not run_git_command("git push -u origin main"):
        print("Не удалось отправить коммиты. Возможно, требуется аутентификация.")
        print("Рекомендации:")
        print("1. Используйте GitHub Desktop для аутентификации")
        print("2. Настройте SSH-ключи для GitHub")
        print("3. Используйте GitHub CLI для аутентификации")
        print("\nПодробнее: https://docs.github.com/en/authentication")
    else:
        print("\nУспешно! Ваш код теперь доступен на GitHub.")
        print(f"URL вашего репозитория: {repo_url}")
        open_repo = input("Открыть репозиторий в браузере? (y/n): ")
        if open_repo.lower() in ['y', 'yes', 'да']:
            # Преобразуем URL, если он заканчивается на .git
            web_url = repo_url
            if web_url.endswith('.git'):
                web_url = web_url[:-4]
            webbrowser.open(web_url)

if __name__ == "__main__":
    main() 