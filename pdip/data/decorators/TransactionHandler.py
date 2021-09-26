# This decorator will check unexpected database error for thread operations
from pdip.data import RepositoryProvider
from pdip.dependency import ServiceProvider


def transaction_handler(func):
    def inner(*args, **kwargs):
        repository_provider = ServiceProvider.injector.get(RepositoryProvider)
        try:
            result = func(*args, **kwargs)
            repository_provider.commit()
            return result
        except Exception as ex:
            repository_provider.rollback()
            print(ex)
            raise
        finally:
            repository_provider.close()

    return inner
