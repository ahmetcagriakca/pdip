# from queue import Queue
# from typing import List
#
# import pandas as pd
# from injector import inject
# from pandas import DataFrame
#
# from ..base import ConnectionAdapter
# from pdip.execution.connection.types.queue.base import QueueProvider
# from ....exceptions import NotSupportedFeatureException
#
#
# class QueueAdapter(ConnectionAdapter):
#     @inject
#     def __init__(self,
#                  queue_provider: QueueProvider,
#                  operation_cache_service: OperationCacheService,
#                  ):
#         self.operation_cache_service = operation_cache_service
#         self.queue_provider = queue_provider
#
#     def clear_data(self, data_integration_id) -> int:
#         target_connection = self.operation_cache_service.get_target_connection(
#             data_integration_id=data_integration_id)
#         target_context = self.queue_provider.get_context(connection=target_connection.Connection)
#         target_context.delete_topic(topic_name=target_connection.Queue.TopicName)
#         target_context.create_topic(topic_name=target_connection.Queue.TopicName)
#         return 1
#
#     def start_source_data_operation(self,
#                                     data_integration_id: int,
#                                     data_operation_job_execution_integration_id: int,
#                                     limit: int,
#                                     process_count: int,
#                                     data_queue: Queue,
#                                     data_result_queue: Queue):
#         source_connection = self.operation_cache_service.get_source_connection(
#             data_integration_id=data_integration_id)
#
#         source_context = self.queue_provider.get_context(connection=source_connection.Connection)
#         source_context.get_unpredicted_data(topic_name=source_connection.Queue.TopicName, group_id="test",
#                                             limit=limit,
#                                             process_count=process_count,
#                                             data_queue=data_queue,
#                                             result_queue=data_result_queue)
#
#     def get_source_data_count(self, data_integration_id) -> int:
#         return -1
#
#     def get_source_data(self, data_integration_id: int, paging_modifier: PagingModifier) -> DataFrame:
#         raise NotSupportedFeatureException("Queue Get Source Data")
#
#     def prepare_data(self, data_integration_id: int, source_data: List[any]) -> List[any]:
#         data_integration_columns = self.operation_cache_service.get_columns_by_integration_id(
#             data_integration_id=data_integration_id)
#
#         source_columns = [(data_integration_column.SourceColumnName) for data_integration_column in
#                           data_integration_columns]
#         if isinstance(source_data, pd.DataFrame):
#             data = source_data[source_columns]
#             prepared_data = data.values.tolist()
#         else:
#             prepared_data = self.prepare_insert_row(data=source_data, columns=source_columns)
#         return prepared_data
#
#     def write_target_data(self, data_integration_id: int, prepared_data: List[any], ) -> int:
#         target_connection = self.operation_cache_service.get_target_connection(
#             data_integration_id=data_integration_id)
#
#         target_context = self.queue_provider.get_context(connection=target_connection.Connection)
#         data_integration_columns = self.data_integration_column_service.get_columns_by_integration_id(
#             data_integration_id=data_integration_id)
#         columns = [(data_integration_column.TargetColumnName) for data_integration_column in
#                    data_integration_columns]
#         df = pd.DataFrame(prepared_data, columns=columns)
#         data = df.where(pd.notnull(df), None)
#         affected_row_count = target_context.write_data(
#             topic_name=target_connection.Queue.TopicName, messages=data)
#         return affected_row_count
#
#     def do_target_operation(self, data_integration_id: int) -> int:
#         raise NotSupportedFeatureException("Queue Target Operation")
