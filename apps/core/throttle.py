"""Tiny cache-based rate limiting (no extra dependencies)."""
from django.conf import settings
from django.core.cache import cache

def client_ip(request):
    if settings.BEHIND_PROXY:
        xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if xff:
            return xff.split(",")[-1].strip()  # last entry = added by our own proxy, not spoofable by the client
    return request.META.get("REMOTE_ADDR", "")

def count(key):
    return cache.get("thr:" + key, 0)

def hit(key, window):
    k = "thr:" + key
    try:
        return cache.incr(k)
    except ValueError:
        cache.add(k, 1, window)
        return 1

def reset(key):
    cache.delete("thr:" + key)
