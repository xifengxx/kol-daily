"""统一网络出口设置：把 macOS 系统代理导出成环境变量。

背景（2026-09-13 实测，排障结论）
---------------------------------
本机开着 macOS **系统代理**（Clash Verge，127.0.0.1:7890）。各库对系统代理的
读取行为并不一致：

===============  ==================  ==========================
库 / 工具         读 macOS 系统代理？   实测结果
===============  ==================  ==========================
requests / urllib  ✅ 读              正常（Yahoo 200）
curl               ❌ 只认环境变量      403
curl_cffi          ❌ 只认环境变量      YFRateLimitError
===============  ==================  ==========================

`yfinance` 底层用 `curl_cffi`，属于最后一种：它会**裸连**出去，撞上 Yahoo 对
国内直连 IP 的封锁（403 / YFRateLimitError），而同一台机器上其它脚本却一切
正常——极易被误判成「Yahoo 封了本机 IP」。实际是「代理没被这个库用上」。

`fetch_industry_chain_heat.py` 是当前唯一依赖 yfinance 的脚本，故由它调用本模块。
其它脚本（requests / urllib）无需处理，系统代理会自动生效。

用法
----
在脚本入口处调用一次即可，必须在 import yfinance **之前**：

    import net_env
    net_env.ensure_proxy()
    import yfinance as yf

优先级：已有 http_proxy/https_proxy 环境变量 > DAILY_BRIEFING_PROXY > 系统代理。
"""

import os
import urllib.request

__all__ = ["ensure_proxy"]

_PROXY_ENV_KEYS = ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy",
                   "ALL_PROXY", "all_proxy")


def _export(https_url, socks_url=None):
    """把代理写进环境变量，供 curl / curl_cffi 等只认环境变量的库使用。"""
    os.environ["HTTPS_PROXY"] = https_url
    os.environ["HTTP_PROXY"] = https_url
    os.environ["https_proxy"] = https_url
    os.environ["http_proxy"] = https_url
    # curl_cffi / requests 也认 ALL_PROXY（对 socks 场景有用）
    os.environ["ALL_PROXY"] = socks_url or https_url
    os.environ["all_proxy"] = socks_url or https_url


def ensure_proxy(verbose=True):
    """确保进程内已导出代理环境变量。返回实际使用的代理 URL，找不到则返回 None。

    幂等：已设置过就直接返回，不会反复改写。
    """
    for key in _PROXY_ENV_KEYS:
        value = os.environ.get(key)
        if value:
            if verbose:
                print(f"  · 代理已设置（{key}），沿用：{value}")
            return value

    override = os.environ.get("DAILY_BRIEFING_PROXY")
    if override:
        _export(override)
        if verbose:
            print(f"  · 使用 DAILY_BRIEFING_PROXY：{override}")
        return override

    # getproxies() 在 macOS 上会读系统网络配置（scutil --proxy）
    proxies = urllib.request.getproxies()
    https_url = proxies.get("https") or proxies.get("http")
    if https_url:
        _export(https_url, proxies.get("socks"))
        if verbose:
            print(f"  · 已从系统代理导出环境变量：{https_url}")
        return https_url

    if verbose:
        print("  ⚠ 未发现系统代理，也未设置 HTTPS_PROXY / DAILY_BRIEFING_PROXY。")
        print("    若目标站点（如 Yahoo Finance）在国内需代理，请显式设置后重试，")
        print("    否则 yfinance 会因裸连而报 YFRateLimitError。")
    return None
