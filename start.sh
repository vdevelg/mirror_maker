# путь до каталога этого скрипта
SCRIPT_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"

shopt -s expand_aliases
alias add_cron_task="~/.local/bin/uv run $SCRIPT_DIR/add_cron_task.py"

start_mirror_maker () {
    cd $SCRIPT_DIR
    ~/.local/bin/uv run $SCRIPT_DIR/main.py
}
# alias start_mirror_maker="~/.local/bin/uv run $SCRIPT_DIR/main.py"

# если скрипт запущен находясь в его каталоге (как правило пользователем), то добавить задачу cron
# если скрипт запущен не из текущего каталога (то есть сторонней программой), то запустить целевую команду
[ "$PWD" = "$SCRIPT_DIR" ] && add_cron_task || start_mirror_maker
