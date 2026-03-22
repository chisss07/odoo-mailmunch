from app.workers.worker import parse_redis_url


def test_parse_redis_url_with_port():
    settings = parse_redis_url("redis://myhost:6380")
    assert settings.host == "myhost"
    assert settings.port == 6380


def test_parse_redis_url_default_port():
    settings = parse_redis_url("redis://myhost")
    assert settings.host == "myhost"
    assert settings.port == 6379


def test_parse_redis_url_with_password_and_db():
    settings = parse_redis_url("redis://:secret@myhost:6380/2")
    assert settings.host == "myhost"
    assert settings.port == 6380
    assert settings.password == "secret"
    assert settings.database == 2
