#!/data/data/com.termux/files/usr/bin/bash

echo "正在连接 adb ..."
adb connect 192.168.0.100:46503
if [ $? -eq 0 ]; then
    echo "adb 连接成功"
else
    echo "adb 连接失败，请检查设备或网络"
fi

# 保存目录（自动创建，以防万一）
SAVE_DIR="/storage/emulated/0/termux"
echo "保存目录: $SAVE_DIR"

while true; do
    # 生成时间文件名：年-月.日-时.分.秒.jpg
    filename="$(date '+%Y-%-m.%-d-%H.%M.%S').jpg"
    echo "=============================="
    adb shell am force-stop com.termux.api
    echo "开始DCIM前 - 文件名: $filename"

    # 后台执行前置摄像头DCIM（-c 1 为前置）
    /data/data/com.termux/files/usr/bin/termux-camera-photo -c 1 "$SAVE_DIR/$filename" &
    pid=$!
    echo "DCIM进程已启动 (PID: $pid)"

    # 动态倒计时6秒（与DCIM同时进行）
    for i in {6..1}; do
        printf "\r倒计时: %d 秒 " "$i"
        sleep 1
    done
    printf "\n倒计时结束\n"

    # 等待DCIM完成
    wait $pid
    if [ $? -eq 0 ]; then
        echo "DCIM完成，文件保存至: $SAVE_DIR/$filename"
    else
        echo "DCIM可能失败，请检查 Termux:API 和摄像头权限"
    fi

    # 强制停止 Termux:API
    echo "正在停止 Termux:API ..."
    adb shell am force-stop com.termux.api
    if [ $? -eq 0 ]; then
        echo "已成功停止 Termux:API"
    else
        echo "停止 Termux:API 命令执行失败（请确认 adb 连接有效）"
    fi
done