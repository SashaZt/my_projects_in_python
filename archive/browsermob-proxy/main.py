def main():
    from browsermobproxy import Server
    import requests
    server = Server(r"c:\Program Files (x86)\browsermob-proxy\bin\browsermob-proxy")

    # Укажите путь к директории browsermob-proxy

    server.start()
    proxy = server.create_proxy()
    print(f'Proxy URL: {proxy.proxy}')  # Добавьте эту строку для проверки
    # Настройка параметров прокси для requests
    proxies = {
        "http": f'http://{proxy.proxy}',
        "https": f'http://{proxy.proxy}'
    }
    # Включение захвата HAR
    proxy.new_har("youtube")
    # Совершение запроса через прокси
    response = requests.get("https://www.youtube.com/watch?v=Krju13Nphgc", proxies=proxies)

    har_data = proxy.har
    # Просмотр данных HAR
    # print(proxy.har)
    entries = har_data["log"]["entries"]
    media_files = []

    for entry in entries:
        response = entry["response"]
        content_type = response["content"]["mimeType"]

        # проверяем MIME-тип содержимого
        if "audio" in content_type or "video" in content_type:
            # если это аудио или видео, сохраняем URL
            media_files.append(entry["request"]["url"])

    print(media_files)
    # Остановка прокси-сервера
    server.stop()


if __name__ == '__main__':
    main()
