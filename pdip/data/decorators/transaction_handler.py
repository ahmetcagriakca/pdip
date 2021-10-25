# This decorator will check unexpected database error for thread operations
from ...data import RepositoryProvider
from ...dependency.container import DependencyContainer


def transactionhandler(func):
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
