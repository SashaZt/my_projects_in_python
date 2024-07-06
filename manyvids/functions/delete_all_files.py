def delete_all_files():
    """
    Функция для удаления временных файлов по всем папкам
    """
    all_path = [chat_path, daily_sales_path, payout_history_path, pending_custom_path]

    for path in all_path:
        # Получаем список всех файлов в директории
        files = glob.glob(os.path.join(path, "*"))
        for f in files:
            # Проверяем, является ли путь файлом
            if os.path.isfile(f):
                os.remove(f)  # Удаляем файл
            elif os.path.isdir(f):
                # Если нужно удалить и поддиректории, раскомментируйте следующие строки
                # for subfile in glob.glob(os.path.join(f, '*')):
                #     os.remove(subfile)  # Удаляем файлы в поддиректории
                # os.rmdir(f)  # Удаляем саму поддиректорию
                print(f"Directory {f} skipped.")
