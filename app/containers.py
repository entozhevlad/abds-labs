from threading import Lock

from dependency_injector import containers, providers

from app.db import ClickHouse
from app.services.energosbyt import EnergosbytService


class Container(containers.DeclarativeContainer):
    """Создаёт зависимости приложения."""

    database = providers.ThreadSafeSingleton(ClickHouse)
    write_lock = providers.ThreadSafeSingleton(Lock)
    service = providers.Factory(EnergosbytService, db=database, write_lock=write_lock)
