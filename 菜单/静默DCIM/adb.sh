#!/data/data/com.termux/files/usr/bin/bash
# 无线调试配对 + 连接脚本
# 使用方法：./adb_pair.sh

# 检查 adb 是否安装
if ! command -v adb &> /dev/null; then
  echo "错误：未找到 adb，请先安装 android-tools"
  echo "运行：pkg install android-tools"
  exit 1
fi

# 输入配对地址（ip:端口）
echo -n "请输入配对地址 (例如 192.168.1.5:12345): "
read pair_addr

# 简单校验地址格式
if [[ ! "$pair_addr" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+$ ]]; then
  echo "错误：地址格式不正确，应为 ip:port"
  exit 1
fi

# 隐藏输入配对码
echo -n "请输入 6 位配对码: "
read -s pair_code
echo

# 自动将配对码传给 adb pair
echo "正在配对，请稍候..."
result=$(echo "$pair_code" | adb pair "$pair_addr" 2>&1)
exit_code=$?

# 判断结果
if [ $exit_code -eq 0 ] && echo "$result" | grep -q "Successfully"; then
  echo "配对成功！"
  # --- 配对成功后询问连接地址 ---
  echo "现在可以连接到设备进行调试。"
  echo -n "请输入连接地址 (格式 ip:port，例如 192.168.1.5:5555): "
  read connect_addr

  # 校验连接地址格式
  if [[ ! "$connect_addr" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+$ ]]; then
    echo "错误：连接地址格式不正确，跳过连接"
    echo "你可以稍后手动连接：adb connect <ip>:<port>"
    exit 0
  fi

  echo "正在连接 ${connect_addr}..."
  adb connect "$connect_addr"
else
  echo "配对失败，请检查："
  echo "1. 配对码是否正确"
  echo "2. 地址和端口是否与无线调试界面显示的配对端口一致"
  echo "3. 设备是否在同一 Wi-Fi 网络"
  echo "错误输出：$result"
  exit 1
fi