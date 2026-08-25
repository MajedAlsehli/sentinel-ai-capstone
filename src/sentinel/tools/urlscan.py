import requests
from langchain_core.tools import tool

@tool
def scan_url(url: str) -> dict:
    """Search urlscan.io's live public index for prior scans of a URL."""

    response = requests.get(
        "https://urlscan.io/api/v1/search/",
        params={"q": f'page.url:"{url}"'},
        timeout=20,
        headers={"User-Agent": "Sentinel-AI-Capstone/1.0"},
    )
    response.raise_for_status()
    data = response.json()
    compact_results = []
    for item in data.get("results", [])[:3]:
        page = item.get("page", {})
        task = item.get("task", {})
        compact_results.append(
            {
                "url": page.get("url"),
                "domain": page.get("domain"),
                "ip": page.get("ip"),
                "country": page.get("country"),
                "scan_time": task.get("time"),
                "result_url": task.get("reportURL"),
            }
        )
    return {
        "status": "ok",
        "provider": "urlscan.io",
        "query_url": url,
        "total": data.get("total", 0),
        "results": compact_results,
    }
