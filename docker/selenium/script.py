from mitmproxy import http


def request(flow: http.HTTPFlow) -> None:
    # Записываем все перехваченные запросы в файл
    with open("/scripts/requests.log", "a", encoding="utf-8") as f:
        f.write(f"Request URL: {flow.request.url}\n")
        f.write(f"Request Method: {flow.request.method}\n")
        f.write(f"Request Headers: {flow.request.headers}\n")
        f.write(f"Request Content: {flow.request.content}\n\n")
