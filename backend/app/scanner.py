import ipaddress
import platform
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any


MAX_SCAN_HOSTS = 256


def parse_network(cidr: str) -> ipaddress.IPv4Network:
    try:
        network = ipaddress.ip_network(cidr.strip(), strict=False)
    except ValueError as exc:
        raise ValueError("网段格式无效，例如 192.168.1.0/24") from exc
    if network.version != 4:
        raise ValueError("仅支持 IPv4 网段")
    hosts = list(network.hosts())
    if not hosts:
        raise ValueError("该网段没有可扫描的主机地址")
    if len(hosts) > MAX_SCAN_HOSTS:
        raise ValueError(f"网段主机数过多，最多支持 /24（{MAX_SCAN_HOSTS} 个地址）")
    return network


def _ping_once(ip: str, timeout_ms: int) -> tuple[bool, int | None]:
    system = platform.system().lower()
    if system == "windows":
        cmd = ["ping", "-n", "1", "-w", str(max(100, timeout_ms)), ip]
    else:
        timeout_s = max(1, (timeout_ms + 999) // 1000)
        cmd = ["ping", "-c", "1", "-W", str(timeout_s), ip]

    started = time.perf_counter()
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=(timeout_ms / 1000.0) + 2,
            check=False,
        )
        latency = int((time.perf_counter() - started) * 1000)
        if completed.returncode == 0:
            return True, latency
        return False, None
    except (subprocess.TimeoutExpired, OSError):
        return False, None


def scan_subnet(
    cidr: str,
    timeout_ms: int = 800,
    concurrency: int = 64,
) -> dict[str, Any]:
    network = parse_network(cidr)
    hosts = [str(ip) for ip in network.hosts()]
    timeout_ms = max(200, min(timeout_ms, 3000))
    concurrency = max(1, min(concurrency, 128))

    results: list[dict[str, Any]] = []
    started = time.perf_counter()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        future_map = {
            executor.submit(_ping_once, ip, timeout_ms): ip for ip in hosts
        }
        for future in as_completed(future_map):
            ip = future_map[future]
            alive, latency = future.result()
            results.append(
                {
                    "ip_address": ip,
                    "alive": alive,
                    "latency_ms": latency,
                }
            )

    results.sort(key=lambda item: tuple(int(part) for part in item["ip_address"].split(".")))
    alive_count = sum(1 for item in results if item["alive"])
    duration_ms = int((time.perf_counter() - started) * 1000)

    return {
        "cidr": str(network),
        "scanned": len(results),
        "alive": alive_count,
        "offline": len(results) - alive_count,
        "duration_ms": duration_ms,
        "hosts": results,
    }
