from .base_config import BaseConfig


class ApsConfig(BaseConfig):
    def __init__(self,
                 coalesce: bool = None,
                 max_instances: str = None,
                 thread_pool_executer_count: bool = None,
                 process_pool_executer_count: int = None,
                 default_misfire_grace_time_date_job: int = None,
                 default_misfire_grace_time_cron_job: int = None

                 ):
        self.process_pool_executer_count = process_pool_executer_count
        self.thread_pool_executer_count = thread_pool_executer_count
        self.max_instances = max_instances
        self.coalesce = coalesce
        self.default_misfire_grace_time_date_job = default_misfire_grace_time_date_job
        self.default_misfire_grace_time_cron_job = default_misfire_grace_time_cron_job
