from dataclasses import dataclass

from ..base.base_config import BaseConfig


@dataclass
class ApsConfig(BaseConfig):
    coalesce: bool = None
    max_instances: str = None
    thread_pool_executer_count: bool = None
    process_pool_executer_count: int = None
    default_misfire_grace_time_date_job: int = None
    default_misfire_grace_time_cron_job: int = None
