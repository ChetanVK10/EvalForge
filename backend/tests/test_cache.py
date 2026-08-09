import pytest
from unittest.mock import MagicMock, patch
from app.services.cache_service import CacheService, cache_service

def test_cache_miss_and_set():
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True

    svc = CacheService(redis_url="redis://localhost:6379/0")
    svc._client = mock_redis

    assert svc.get("test_key") is None
    mock_redis.get.assert_called_once_with("test_key")

    assert svc.set("test_key", "test_val", ttl_seconds=30) is True
    mock_redis.set.assert_called_once_with("test_key", "test_val", ex=30)

def test_cache_hit():
    mock_redis = MagicMock()
    mock_redis.get.return_value = '{"foo": "bar"}'

    svc = CacheService(redis_url="redis://localhost:6379/0")
    svc._client = mock_redis

    assert svc.get("test_key") == '{"foo": "bar"}'

def test_cache_fail_open_on_redis_error():
    mock_redis = MagicMock()
    mock_redis.get.side_effect = Exception("Redis connection lost")
    mock_redis.set.side_effect = Exception("Redis connection lost")

    svc = CacheService(redis_url="redis://localhost:6379/0")
    svc._client = mock_redis

    # Redis error must fail-open and return None/False without crashing
    assert svc.get("test_key") is None
    assert svc.set("test_key", "val") is False

def test_cache_delete():
    mock_redis = MagicMock()
    mock_redis.delete.return_value = True

    svc = CacheService(redis_url="redis://localhost:6379/0")
    svc._client = mock_redis

    assert svc.delete("test_key") is True
    mock_redis.delete.assert_called_once_with("test_key")
