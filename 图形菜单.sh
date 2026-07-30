#!/bin/bash
# ===========================================
# 菜单导航脚本 (fzf) - 精简版
# ===========================================
set -euo pipefail

BASE="菜单"
if [ ! -d "$BASE" ]; then
    BASE="$(dirname "$0")/菜单"
    if [ ! -d "$BASE" ]; then
        echo "❌ 未找到“菜单”目录" >&2; exit 1
    fi
fi
cd "$BASE" || exit 1
BASE_DIR="$PWD"
cd - > /dev/null
current="$BASE_DIR"

while true; do
    [ -d "$current" ] || { echo "❌ 目录失效: $current" >&2; exit 1; }
    cd "$current" || exit 1

    dirs=$(find . -maxdepth 1 -mindepth 1 -type d -printf '%f\n' 2>/dev/null | sort)

    if [ -n "$dirs" ]; then
        # 子目录菜单
        menu=()
        [ "$current" != "$BASE_DIR" ] && menu+=("🔙 返回")
        while IFS= read -r d; do
            menu+=("$d")
        done < <(echo "$dirs" | sort -r)
        menu+=("❌ 退出")

        choice=$(printf '%s\n' "${menu[@]}" | fzf \
            --prompt="📂 ${current#$BASE_DIR}/ > " \
            --header="ENTER:进入  |  ESC:返回" \
            --layout=reverse \
            --no-mouse)

        if [ -z "$choice" ]; then
            [ "$current" != "$BASE_DIR" ] && current=$(dirname "$current") || { echo "再见！"; exit 0; }
        elif [ "$choice" = "🔙 返回" ]; then
            current=$(dirname "$current")
        elif [ "$choice" = "❌ 退出" ]; then
            echo "再见！"; exit 0
        else
            current="$current/$choice"
        fi

    else
        # 脚本选择
        scripts=$(find . -maxdepth 1 -type f \( -name "*.sh" -o -name "*.py" \) -printf '%f\n' | sort)
        if [ -z "$scripts" ]; then
            echo "⚠️ 该目录没有脚本文件"
            read -p "按回车返回..." -r
            current=$(dirname "$current")
            continue
        fi

        menu=()
        [ "$current" != "$BASE_DIR" ] && menu+=("🔙 返回")
        while IFS= read -r s; do
            menu+=("$s")
        done < <(echo "$scripts" | sort -r)
        menu+=("❌ 退出")

        script_choice=$(printf '%s\n' "${menu[@]}" | fzf \
            --prompt="▶ 选择脚本: " \
            --header="ENTER:执行  |  ESC:返回" \
            --layout=reverse \
            --no-mouse)

        if [ -z "$script_choice" ]; then
            current=$(dirname "$current")
            continue
        elif [ "$script_choice" = "🔙 返回" ]; then
            current=$(dirname "$current")
            continue
        elif [ "$script_choice" = "❌ 退出" ]; then
            echo "再见！"; exit 0
        else
            clear
            echo -e "\033[1;32m▶ 执行: $script_choice\033[0m"
            echo "--------------------------------"
            if [[ "$script_choice" == *.sh ]]; then
                bash "$current/$script_choice"
            elif [[ "$script_choice" == *.py ]]; then
                if command -v python3 &>/dev/null; then
                    python3 "$current/$script_choice"
                else
                    python "$current/$script_choice"
                fi
            fi
            echo "--------------------------------"
            echo -e "\033[1;32m✅ 脚本执行完毕，按回车返回...\033[0m"
            read -r
            current=$(dirname "$current")
        fi
    fi
done