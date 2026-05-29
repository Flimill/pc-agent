import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion  # ← Для Paho v2
import psutil
import subprocess
import json
import time
import threading

# 🔑 КОНФИГУРАЦИЯ (ПК как устройство — только свои учётные данные)
BROKER = "mqtt.cloud.yandex.net"
PORT = 8883
CA_CERT = "rootca.crt"

DEVICE_ID = "aretnchf4d2cmqqbnanv"  # ← ID устройства ПК
PASSWORD = "1234567890_qwer"         # ← пароль этого устройства

TOPIC_EVENTS = f"$devices/{DEVICE_ID}/events"      # ПК публикует мониторинг сюда
TOPIC_COMMANDS = f"$devices/{DEVICE_ID}/commands"  # ПК подписывается на команды отсюда

# ✅ on_connect для Paho v2 (5 аргументов)
def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"✅ Подключено к MQTT (код: {reason_code})")
    client.subscribe(TOPIC_COMMANDS)
    print(f"📥 Подписка на команды: {TOPIC_COMMANDS}")

# ✅ on_message для Paho v2 (5 аргументов)
def on_message(client, userdata, msg):
    cmd = msg.payload.decode().strip()
    print(f"📩 Получена команда: {cmd}")
    
    if cmd == "POWER_OFF":
        print("🛑 Выполняется выключение...")
        subprocess.run(["shutdown", "/s", "/f", "/t", "0"])
    elif cmd == "RESTART":
        print("🔄 Выполняется перезагрузка...")
        subprocess.run(["shutdown", "/r", "/f", "/t", "0"])
    elif cmd == "POWER_ON":
        print("💡 POWER_ON требует Wake-on-LAN")
    else:
        print(f"❓ Неизвестная команда: {cmd}")

def on_message(client, userdata, msg):
    cmd = msg.payload.decode().strip()
    print(f"📩 Получена команда: {cmd}")
    
    if cmd == "POWER_OFF":
        print("🛑 Выполняется выключение...")
        subprocess.run(["shutdown", "/s", "/f", "/t", "0"])
    elif cmd == "RESTART":
        print("🔄 Выполняется перезагрузка...")
        subprocess.run(["shutdown", "/r", "/f", "/t", "0"])
    elif cmd == "POWER_ON":
        print("💡 POWER_ON требует Wake-on-LAN")
    else:
        print(f"❓ Неизвестная команда: {cmd}")

def publish_monitoring(client):
    """Фоновый поток: сбор и отправка метрик"""
    while True:
        try:
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            uptime_sec = int(time.time() - psutil.boot_time())
            days, rem = divmod(uptime_sec, 86400)
            hours, _ = divmod(rem, 3600)
            
            payload = json.dumps({
                "cpu": f"{cpu}%",
                "ram": f"{ram}%",
                "uptime": f"{days}d {hours}h"
            })
            client.publish(TOPIC_EVENTS, payload, qos=1)
            print(f"📤 Мониторинг: {payload}")
        except Exception as e:
            print(f"⚠️ Ошибка мониторинга: {e}")
        time.sleep(5)

def main():
    # ✅ Paho v2: указываем CallbackAPIVersion
    client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id="pc-agent")
    
    # ✅ ИСПРАВЛЕНО: используем DEVICE_ID и PASSWORD (не реестр!)
    client.username_pw_set(DEVICE_ID, PASSWORD)
    client.tls_set(ca_certs=CA_CERT)
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"🌐 Подключение к {BROKER}:{PORT}...")
    client.connect(BROKER, PORT, 60)
    
    # Запуск потока мониторинга
    threading.Thread(target=publish_monitoring, args=(client,), daemon=True).start()
    
    print("🟢 Агент запущен. Ожидание команд...")
    client.loop_forever()

if __name__ == "__main__":
    main()