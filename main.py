import os
import tomllib
import urllib.request
from pathlib import Path

import requests
from dotenv import load_dotenv
from git import Repo
from git.exc import InvalidGitRepositoryError


def load_configuration(file):
    # принудительная перезапись переменных среды, если они были ранее загружены IDE.
    # Помогло решить проблему с неверным парсингом инлайн комментария:
    load_dotenv(override=True)
    with open(file, 'r', encoding='utf-8') as f:
        raw_toml = f.read()
    expanded_toml = os.path.expandvars(raw_toml)
    return tomllib.loads(expanded_toml)

def direct_download(url: str, path: Path) -> None:
    with urllib.request.urlopen(url) as response, open(path, 'wb') as file:
        file.write(response.read())
    print(f"Файл {Path(path).name} успешно загружен в {path.parent}")

def has_local_repo_ahead_commits(repo: Repo) -> bool:
    # 1. Скачиваем актуальное состояние с удаленного сервера
    origin = repo.remotes.origin
    origin.fetch()

    # 2. Получаем активную ветку
    active_branch_name = repo.active_branch.name

    # 3. Ссылки на локальный и удаленный коммиты
    local_commit = repo.head.commit
    remote_commit = repo.commit(f"origin/{active_branch_name}")

    # 4. Сравниваем хэши
    if local_commit.hexsha != remote_commit.hexsha:
        # Проверяем есть ли в локальном репозитории более поздние коммиты относительно удалённого
        return len(list(repo.iter_commits(f"origin/{active_branch_name}..HEAD"))) > 0

def is_git_repo(path: str) -> bool:
    try:
        _ = Repo(path).git_dir
        return True
    except InvalidGitRepositoryError:
        return False

def git_commit_file(path: Path) -> None:
    # Ссылка для авторизации по токену
    REMOTE_URL = f"https://" \
        f"{cfg['gitverse']['token']}@gitverse.ru/" \
        f"{cfg['gitverse']['owner']}/{cfg['gitverse']['repo_name']}.git"

    # 1. Клонирование репозитория (если в папке его нет)
    if not (path.parent.exists() and is_git_repo(path.parent)):
        repo = Repo.clone_from(REMOTE_URL, path.parent)
    else:
        repo = Repo(path.parent)

    # 2. Скачивание файла внутрь локального репозитория
    direct_download(cfg['url'], path)

    origin = repo.remote(name="origin")
    if repo.is_dirty(untracked_files=True):  # в локальном репозитории есть незафиксированные изменения
        print("В локальном репозитории есть изменения.")
        repo.index.add([Path(path).name])  # git add
        repo.index.commit("Обнова")  # git commit
        origin.push()  # git push
    else:  # в локальном репозитории нет изменений
        if has_local_repo_ahead_commits(repo):  # локальный репозиторий имеет более поздние коммиты относительно удалённого
            print("Удалённый репозиторий не синхронизирован с локальным.")
            origin.push()  # git push
        else:
            print("Удалённый репозиторий синхронизирован с локальным. Нет изменений для загрузки на Gitverse")
            return
    send_telegram_message("Proxy Mirror: на Gitverse обновился файл 26.txt")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{cfg['telegram']['token']}/sendMessage"
    payload = {
        "chat_id": cfg['telegram']['chat_id'],
        "text": message,
        "disable_notification": True,  # Отключение звука уведомлений
    }
    response = requests.post(url, data=payload)
    return response.json()

def main():
    global cfg
    cfg = load_configuration("config.toml")
    data_file_path = Path(cfg['data_dir']) / Path(cfg['url']).name
    try:
        git_commit_file(data_file_path)
    except Exception as err:  # noqa: BLE001
        send_telegram_message(f"Proxy Mirror: ОШИБКА\n{err!s}")
        print(f"Ошибка: {err!s}")

if __name__ == "__main__":
    main()
