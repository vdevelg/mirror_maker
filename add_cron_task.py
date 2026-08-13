import subprocess

# минуты (0-59), часы (0-23), день месяца (1-31), месяц (1-12), день недели (0-7, 7-это воскресенье)
cron_command = "/root/mirror_maker/start.sh"
log_file = "/var/log/mirror_maker.log"
cron_task = f"*/5 * * * * {cron_command} &> {log_file}"  # выполнять каждые 5 минут и перенаправлять вывод stdout и stderr в лог

# Получаем текущий crontab
result = subprocess.run(['crontab', '-l'], capture_output=True, text=True, check=False)
current_crontab = result.stdout if result.returncode == 0 else ""

for line in current_crontab.splitlines():
    stripped_line = line.strip()
    if (stripped_line and  # если строка не пустая
        not stripped_line.startswith('#') and  # и не является комментарием
        cron_command in stripped_line):  # если в строке есть команда, которую мы ищем
        stripped_task_line = stripped_line.partition("#")[0].strip()  # удаляем комментарий, если он есть
        new_line = line.replace(stripped_task_line, cron_task)
        break

# Проверяем наличие задачи
if cron_command in current_crontab:
    if line and new_line and line == new_line:
        print("Задача cron уже существует и не требует изменений.")
    else:
        new_crontab = current_crontab.replace(line, new_line)
        subprocess.run(['crontab', '-'], input=new_crontab, text=True, check=False)
        print("Существующая задача cron обновлена.")
else:
    # Добавляем задачу, если её нет
    if current_crontab and not current_crontab.endswith('\n'):
        current_crontab += '\n'
    new_crontab = current_crontab + cron_task + "\n"
    subprocess.run(['crontab', '-'], input=new_crontab, text=True, check=False)
    print("Новая задача cron добавлена.")
