from __future__ import annotations

import threading

from pymilvus import MilvusClient
from shared.settings import MilvusSettings


class SingletonMeta(type):
    _instance: dict = {}
    _lock: threading.Lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instance:
                instance = super().__call__(*args, **kwargs)
                cls._instance[cls] = instance
        return cls._instance

    def clear(cls):
        with cls._lock:
            _ = cls._instance.pop(cls, None)


class MilvusDriver(metaclass=SingletonMeta):
    _driver: MilvusClient

    def __init__(self, settings: MilvusSettings):
        try:
            self._driver = MilvusClient(
                uri=self._build_uri(settings.host, settings.port),
                user=settings.user,
                password=settings.password,
                db_name=settings.db_name,
            )
        except Exception:
            raise

    def _build_uri(self, host: str, port: int) -> str:
        return f'http://{host}:{port}'

    @property
    def driver(self) -> MilvusClient:
        try:
            return self._driver
        except Exception:
            raise

    def close(self):
        try:
            self._driver.close()
        except AttributeError:
            pass
        finally:
            self.__class__.clear()

    def __del__(self):
        self.close()
