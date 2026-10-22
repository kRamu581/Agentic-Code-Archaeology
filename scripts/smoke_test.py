"""Check the locally running backend and Vite UI before a live demo."""
from urllib.error import URLError
from urllib.request import urlopen


CHECKS = (
    ("backend health", "http://127.0.0.1:8000/"),
    ("history API", "http://127.0.0.1:8000/analysis-history"),
    ("GitHub connection status", "http://127.0.0.1:8000/github/status"),
    ("frontend dashboard", "http://localhost:5173/"),
    ("frontend history route", "http://localhost:5173/history"),
    ("frontend compare route", "http://localhost:5173/compare"),
)


def main() -> int:
    failed = []
    for name, url in CHECKS:
        try:
            with urlopen(url, timeout=5) as response:
                if response.status != 200:
                    raise URLError(f"unexpected HTTP status {response.status}")
                response.read(1024)
            print(f"PASS {name}: {url}")
        except (OSError, URLError) as error:
            failed.append(name)
            print(f"FAIL {name}: {error}")
    if failed:
        print(f"\n{len(failed)} smoke check(s) failed: {', '.join(failed)}")
        return 1
    print("\nAll demo smoke checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
