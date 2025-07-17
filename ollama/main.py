import json
import time

import requests
from scrapegraphai.graphs import SmartScraperGraph

# Определяем конфигурацию
graph_config = {
    "llm": {
        "model": "ollama/llama3.2:3b",
        "temperature": 0.1,
        "format": "json",
        "base_url": "http://localhost:11434",
    },
    "embeddings": {
        "model": "ollama/nomic-embed-text",
        "base_url": "http://localhost:11434",
    },
    "verbose": True,
    "headless": True,
}


def compare_methods(url, ollama_prompt, scrapegraph_prompt):
    """Сравнение прямого API Ollama vs ScrapeGraphAI"""

    print(f"Тестируем URL: {url}")

    # Метод 1: Прямой API Ollama
    start_time = time.time()

    try:
        page_response = requests.get(url)
        html_content = page_response.text

        payload = {
            "model": "llama3.2:3b",
            "prompt": f"{ollama_prompt}\n\nHTML:\n{html_content[:5000]}",
            "stream": False,
            "format": "json",
        }

        ollama_response = requests.post(
            "http://localhost:11434/api/generate", json=payload
        )
        ollama_time = time.time() - start_time

        print(f"✅ Прямой Ollama API: {ollama_time:.2f} секунд")

    except Exception as e:
        print(f"❌ Ошибка Ollama API: {e}")
        ollama_response = None
        ollama_time = 0

    # Метод 2: ScrapeGraphAI
    start_time = time.time()

    try:
        scraper = SmartScraperGraph(
            prompt=scrapegraph_prompt,
            source=url,
            config=graph_config,
        )

        scrapegraph_result = scraper.run()
        scrapegraph_time = time.time() - start_time

        print(f"✅ ScrapeGraphAI: {scrapegraph_time:.2f} секунд")

    except Exception as e:
        print(f"❌ Ошибка ScrapeGraphAI: {e}")
        scrapegraph_result = None
        scrapegraph_time = 0

    return {
        "ollama_direct": {
            "time": ollama_time,
            "result": (
                ollama_response.json()
                if ollama_response and ollama_response.status_code == 200
                else None
            ),
        },
        "scrapegraph": {"time": scrapegraph_time, "result": scrapegraph_result},
    }


def safe_print_result(result_data, max_length=300):
    """Безопасный вывод результата"""
    if not result_data:
        return "Нет данных"

    if isinstance(result_data, dict):
        result_str = json.dumps(result_data, indent=2, ensure_ascii=False)
    else:
        result_str = str(result_data)

    if len(result_str) > max_length:
        return result_str[:max_length] + "..."
    return result_str


# Запуск тестов
if __name__ == "__main__":
    # Тест 1: Цитаты (подходящий контент для сайта)
    print("=== ТЕСТ 1: ЦИТАТЫ ===")
    quotes_result = compare_methods(
        "https://quotes.toscrape.com/",
        "Extract all quotes with their authors. Return as JSON array with fields: quote, author",
        "Extract all quotes with their authors from this page",
    )

    print("\n=== РЕЗУЛЬТАТЫ ЦИТАТ ===")
    print("Ollama результат:")
    print(safe_print_result(quotes_result["ollama_direct"]["result"]))

    print("\nScrapeGraphAI результат:")
    print(safe_print_result(quotes_result["scrapegraph"]["result"]))

    print("\n" + "=" * 50 + "\n")

    # Тест 2: Простой HTML для продуктов (создаем тестовую страницу)
    print("=== ТЕСТ 2: ПРОСТАЯ HTML СТРАНИЦА ===")

    # Используем httpbin для тестирования
    simple_result = compare_methods(
        "https://httpbin.org/html",
        "Extract all headings and paragraphs. Return as JSON",
        "Extract all headings and text content from this page",
    )

    print("\n=== РЕЗУЛЬТАТЫ ПРОСТОЙ СТРАНИЦЫ ===")
    print("Ollama результат:")
    print(safe_print_result(simple_result["ollama_direct"]["result"]))

    print("\nScrapeGraphAI результат:")
    print(safe_print_result(simple_result["scrapegraph"]["result"]))
