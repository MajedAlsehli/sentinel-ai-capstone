import requests
from langchain_core.tools import tool

@tool
def geolocate_ip(ip: str) -> dict:
    """Look up live network ownership and location data for an IP address."""

    response = requests.get(
        f"https://ipwho.is/{ip}",
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    return {
        "status": "ok" if data.get("success") else "error",
        "provider": "ipwho.is",
        "ip": data.get("ip", ip),
        "country": data.get("country"),
        "region": data.get("region"),
        "city": data.get("city"),
        "connection": data.get("connection", {}),
        "message": data.get("message"),
    }
