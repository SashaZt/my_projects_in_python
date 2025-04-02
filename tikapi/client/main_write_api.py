import requests
import json
import time
from datetime import datetime, date

API_URL = "https://10.0.0.18:5000/api"

def load_tiktok_data(data_file="tiktok_data.json"):
    """Загрузка данных из JSON-файла"""
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_user(api_url, user_data):
    """Создание пользователя в системе"""
    response = requests.post(
        f"{api_url}/users/", 
        json=user_data,
        verify=False
    )
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 400 and "уже существует" in response.text:
        # Получаем существующего пользователя
        user_response = requests.get(
            f"{api_url}/users/{user_data['tik_tok_id']}",
            verify=False
        )
        if user_response.status_code == 200:
            return user_response.json()
    print(f"Ошибка при создании пользователя: {response.status_code}")
    print(response.text)
    return None

def add_user_stats(api_url, user_id, stats_data):
    """Добавление статистики пользователя"""
    stats_payload = {
        "user_id": user_id,
        "follower_count": stats_data.get("followerCount"),
        "following_count": stats_data.get("followingCount"),
        "friend_count": stats_data.get("friendCount"),
        "heart_count": stats_data.get("heart"),
        "video_count": stats_data.get("videoCount"),
        "timestamp": datetime.now().isoformat()
    }
    
    response = requests.post(
        f"{api_url}/stats/user-stats",
        json=stats_payload,
        verify=False
    )
    return response.status_code == 200

def import_live_streams(api_url, tiktok_id, streams_data):
    """Импорт данных о прямых трансляциях"""
    response = requests.post(
        f"{api_url}/live/import-bulk?tiktok_id={tiktok_id}",
        json=streams_data,
        verify=False
    )
    return response.status_code == 200

def add_analytics(api_url, user_id, analytics_items):
    """Добавление дневной аналитики"""
    success_count = 0
    
    for item in analytics_items:
        if item.get("tik_tok_id") != tiktok_id:
            continue
            
        analytics_data = {
            "user_id": user_id,
            "date": date.fromtimestamp(item["date"]).isoformat(),
            "diamonds_total": item["diamonds_now"],
            "live_duration_total": item["live_duration_now"]
        }
        
        response = requests.post(
            f"{api_url}/live/analytics",
            json=analytics_data,
            verify=False
        )
        
        if response.status_code == 200:
            success_count += 1
    
    return success_count

# Основной код
if __name__ == "__main__":
    try:
        # Загрузка данных
        tiktok_data = {
            "user_info": {
                "tik_tok_id": "7312401215441126406",
                "nickname": "Lizzyyy",
                "unique_id": "lizzyyy0",
                "avatarMedium": "https://example.com/avatar.jpg",
                "followingVisibility": 2,
                "isUnderAge18": False,
                "openFavorite": False,
                "privateAccount": False,
                "signature": "proud to be Ukrainian",
                "followerCount": 8199,
                "followingCount": 364,
                "friendCount": 290,
                "heart": 22100,
                "videoCount": 279
            },
            "user_live_list": {
                "7312401215441126406": [
                    # Данные о трансляциях
                ]
            },
            "user_live_analytics": [
                # Данные аналитики
            ]
        }
        
        # Извлекаем данные пользователя
        user_info = tiktok_data["user_info"]
        tiktok_id = user_info["tik_tok_id"]
        
        # Подготавливаем данные пользователя
        user_data = {
            "tik_tok_id": user_info["tik_tok_id"],
            "nickname": user_info["nickname"],
            "unique_id": user_info["unique_id"],
            "avatar_medium": user_info["avatarMedium"],
            "following_visibility": user_info["followingVisibility"],
            "is_under_age_18": user_info["isUnderAge18"],
            "open_favorite": user_info["openFavorite"],
            "private_account": user_info["privateAccount"],
            "signature": user_info["signature"]
        }
        
        # Шаг 1: Создание пользователя
        print("Создание пользователя...")
        user = create_user(API_URL, user_data)
        if not user:
            print("Не удалось создать пользователя. Завершение.")
            exit(1)
        
        user_id = user["id"]
        print(f"Пользователь создан/получен, ID: {user_id}")
        
        # Шаг 2: Добавление статистики
        print("Добавление статистики...")
        if add_user_stats(API_URL, user_id, user_info):
            print("Статистика пользователя успешно добавлена")
        else:
            print("Ошибка при добавлении статистики")
        
        # Шаг 3: Импорт данных о прямых трансляциях
        print("Импорт данных о трансляциях...")
        streams_data = tiktok_data["user_live_list"].get(tiktok_id, [])
        if import_live_streams(API_URL, tiktok_id, streams_data):
            print(f"Данные о {len(streams_data)} трансляциях успешно импортированы")
        else:
            print("Ошибка при импорте данных о трансляциях")
        
        # Шаг 4: Добавление аналитики
        print("Добавление дневной аналитики...")
        analytics_count = add_analytics(API_URL, user_id, tiktok_data["user_live_analytics"])
        print(f"Добавлено {analytics_count} записей аналитики")
        
        print("Загрузка данных завершена успешно!")
        
    except Exception as e:
        print(f"Произошла ошибка: {e}")