# This decorator will check unexpected database error for thread operations
from pdip.data import RepositoryProvider
from pdip.dependency.container import DependencyContainer


def transaction_handler(func):
    def inner(*args, **kwargs):
        repository_provider = DependencyContainer.Instance.get(RepositoryProvider)
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
