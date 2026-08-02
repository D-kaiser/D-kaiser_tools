#!/data/data/com.termux/files/usr/bin/bash
# 无线调试配对 + 连接脚本（自动读取配置）
# 配置文件：~/D-kaiser_tools/dk配置.conf
# 配置内容示例：
# 局域网ip="192.168.0.100"
# 无线调试连接端口="46503"

# 检查 adb 是否安装
if ! command -v adb &> /dev/null; then
  echo "错误：未找到 adb，请先安装 android-tools"
  echo "运行：pkg install android-tools"
  exit 1
fi

CONF_FILE="$HOME/D-kaiser_tools/dk配置.conf"

# 检查配置文件是否存在
if [ ! -f "$CONF_FILE" ]; then
  echo "错误：配置文件 $CONF_FILE 不存在"
  exit 1
fi

# 读取局域网 IP
target_ip=$(grep -E '^\s*局域网ip\s*=\s*"' "$CONF_FILE" | head -1 | sed 's/.*"\([^"]*\)".*/\1/')
if [ -z "$target_ip" ]; then
  echo "错误：配置文件中未找到 '局域网ip' 或格式不正确"
  exit 1
fi

# 读取无线调试连接端口
connect_port=$(grep -E '^\s*无线调试连接端口\s*=\s*"' "$CONF_FILE" | head -1 | sed 's/.*"\([^"]*\)".*/\1/')
if [ -z "$connect_port" ]; then
  echo "错误：配置文件中未找到 '无线调试连接端口' 或格式不正确"
  exit 1
fi

echo "配置读取成功：目标设备 IP = $target_ip，连接端口 = $connect_port"

# 输入配对端口
echo -n "请输入无线调试配对端口: "
read pair_port
if ! [[ "$pair_port" =~ ^[0-9]+$ ]]; then
  echo "错误：端口必须为数字"
  exit 1
fi

# 隐藏输入配对码
echo -n "请输入 6 位配对码: "
read -s pair_code
echo

# 执行配对
pair_addr="${target_ip}:${pair_port}"
echo "正在配对 $pair_addr ..."
result=$(echo "$pair_code" | adb pair "$pair_addr" 2>&1)
exit_code=$?

if [ $exit_code -eq 0 ] && echo "$result" | grep -q "Successfully"; then
  echo "配对成功！"
  # 使用配置文件中的 IP 和连接端口进行连接
  connect_addr="${target_ip}:${connect_port}"
  echo "正在连接 ${connect_addr} ..."
  adb connect "$connect_addr"
else
  echo "配对失败，请检查："
  echo "1. 配对码是否正确"
  echo "2. 配对端口是否与无线调试界面显示的配对端口一致"
  echo "3. 设备是否在同一 Wi-Fi 网络"
  echo "错误输出：$result"
  exit 1
fi