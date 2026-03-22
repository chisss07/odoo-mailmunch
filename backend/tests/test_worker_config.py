from app.workers.worker import parse_redis_url


def test_parse_redis_url_with_port():
    settings = parse_redis_url("redis://myhost:6380")
    assert settings.host == "myhost"
    assert settings.port == 6380


def test_parse_redis_url_default_port():
    settings = parse_redis_url("redis://myhost")
    assert settings.host == "myhost"
    assert settings.port == 6379
