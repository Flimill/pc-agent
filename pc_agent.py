import paho.mqtt.client as mqtt
import psutil
import subprocess
import json
import time
import threading

# 🔑 КОНФИГУРАЦИЯ (используем учётные данные РЕЕСТРА)
BROKER = "mqtt.cloud.yandex.net"  # ✅ Тот же домен, что работает на телефоне
PORT = 8883
REGISTRY_ID = "arer2s34gviu7tp6mhgu"
REGISTRY_PASSWORD = "1234567890Qwer"
DEVICE_ID = "aremdpnn72hm5bt0bh1p"
CA_CERT = "rootca.crt"

# 📡 Топики (согласовано с вашим Android-приложением)
TOPIC_EVENTS = f"$devices/{DEVICE_ID}/events"      # Телефон публикует команды сюда
TOPIC_COMMANDS = f"$devices/{DEVICE_ID}/commands"   # ПК публикует мониторинг сюда

def on_connect(client, userdata, flags, rc):
    print(f"✅ Подключено к MQTT (код: {rc})")
    client.subscribe(TOPIC_EVENTS)
    print(f"📥 Подписка на команды: {TOPIC_EVENTS}")

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
        print("💡 POWER_ON требует Wake-on-LAN. Отправьте магический пакет с телефона.")
    else:
        print(f"❓ Неизвестная команда: {cmd}")

def publish_monitoring(client):
    """Фоновый поток: собирает метрики каждые 5 сек и шлёт на телефон"""
    while True:
        try:
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            
            uptime_sec = int(time.time() - psutil.boot_time())
            days, rem = divmod(uptime_sec, 86400)
            hours, rem = divmod(rem, 3600)
            uptime_str = f"{days}d {hours}h"
            
            payload = json.dumps({
                "cpu": f"{cpu}%",
                "ram": f"{ram}%",
                "uptime": uptime_str
            })
            
            client.publish(TOPIC_COMMANDS, payload, qos=1)
            print(f"📤 Мониторинг: {payload}")
        except Exception as e:
            print(f"⚠️ Ошибка мониторинга: {e}")
        
        time.sleep(5)  # Интервал отправки

def main():
    client = mqtt.Client(client_id="pc-agent")
    client.username_pw_set(REGISTRY_ID, REGISTRY_PASSWORD)
    client.tls_set(ca_certs=CA_CERT)
    client.on_connect = on_connect
    client.on_message = on_message

    print("🌐 Подключение к Yandex IoT Core...")
    client.connect(BROKER, PORT, 60)
    
    # Запуск потока мониторинга
    monitor_thread = threading.Thread(target=publish_monitoring, args=(client,), daemon=True)
    monitor_thread.start()
    
    print("🟢 Агент запущен. Ожидание команд...")
    client.loop_forever()

if __name__ == "__main__":
    main()