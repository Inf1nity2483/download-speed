import argparse
import sys
import time
from urllib.parse import urlparse

import requests

REQUEST_COUNT = 10
TIMEOUT_SECONDS = 60
CHUNK_SIZE = 64 * 1024


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Замерить скорость скачивания: 10 последовательных запросов."
    )
    parser.add_argument("url", help="Адрес файла, например тяжёлой картинки")
    return parser.parse_args()


def require_http_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        print(f"Нужен абсолютный http(s) URL, получено: {url}", file=sys.stderr)
        raise SystemExit(1)


def download_once(session: requests.Session, url: str) -> tuple[int, float]:
    started = time.perf_counter()
    with session.get(url, stream=True, timeout=TIMEOUT_SECONDS) as response:
        response.raise_for_status()
        total = 0
        # Байты как их отдал сервер, без распаковки Content-Encoding.
        for chunk in response.raw.stream(CHUNK_SIZE, decode_content=False):
            total += len(chunk)
        elapsed = time.perf_counter() - started
    return total, elapsed


def main() -> None:
    args = parse_args()
    require_http_url(args.url)

    session = requests.Session()
    byte_counts: list[int] = []
    durations: list[float] = []

    for index in range(1, REQUEST_COUNT + 1):
        nbytes, elapsed = download_once(session, args.url)
        byte_counts.append(nbytes)
        durations.append(elapsed)
        print(f"{index:2d}  {nbytes} bytes  {elapsed:.3f} s")

    total_bytes = sum(byte_counts)
    total_seconds = sum(durations)
    average_seconds = total_seconds / REQUEST_COUNT
    speed_mbps = (total_bytes * 8) / total_seconds / 1_000_000

    print()
    print(f"requests:   {REQUEST_COUNT}")
    print(f"total:      {total_bytes} bytes")
    print(f"avg time:   {average_seconds:.3f} s")
    print(f"total time: {total_seconds:.3f} s")
    print(f"speed:      {speed_mbps:.2f} Mbit/s")


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as error:
        print(f"Ошибка запроса: {error}", file=sys.stderr)
        raise SystemExit(1)
