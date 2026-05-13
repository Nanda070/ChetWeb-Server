import requests

def send_ticket():
    url = "http://127.0.0.1:8000/api/moderation/tickets/create"
    
    payloads = [
        {"user_id": "ТВОЙ_DISCORD_ID", "content": "Тестовый прогон системы. Жду аппрува в панели."}
    ]
    
    for data in payloads:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"[OK] Тикет от {data['user_id']} успешно доставлен в Control Tower.")
        else:
            print(f"[ERR] Ошибка: {response.text}")

if __name__ == "__main__":
    send_ticket()
