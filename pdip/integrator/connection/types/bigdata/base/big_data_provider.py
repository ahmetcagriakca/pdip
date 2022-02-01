from injector import inject

from .big_data_context import BigDataContext
from .big_data_policy import BigDataPolicy
from ....domain.authentication.basic import ConnectionBasicAuthentication
from ....domain.authentication.kerberos import KerberosAuthentication
from ....domain.authentication.mechanism import MechanismTypes
from ....domain.bigdata import BigDataConnectionConfiguration
from ....domain.enums import ConnectorTypes, ConnectionTypes
from ....domain.server.base import ConnectionServer
from ......dependency import IScoped


class BigDataProvider(IScoped):
    @inject
    def __init__(self):
        pass

    def __initialize_context(self, config: BigDataConnectionConfiguration):
        policy = BigDataPolicy(config=config)
        context = BigDataContext(policy=policy)
        return context

    def get_context_by_config(self, config: BigDataConnectionConfiguration) -> BigDataContext:
        return self.__initialize_context(config=config)

    def get_context(
            self,
            connector_type: ConnectorTypes, mechanism_type: MechanismTypes,
            host: str, port: int,
            user: str, password: str,
            database: str,
            ssl: bool, use_only_sspi: bool) -> BigDataContext:
        """
        Creating Context
        """
        if connector_type == connector_type.Impala:
            config = BigDataConnectionConfiguration(
                ConnectionType=ConnectionTypes.BigData,
                ConnectorType=ConnectorTypes.Impala,
                AuthenticationMechanismType=mechanism_type,
                Server=ConnectionServer(Host=host, Port=port),
                BasicAuthentication=ConnectionBasicAuthentication(User=user,
                                                                  Password=password),
                KerberosAuthentication=KerberosAuthentication(Principal=user, Password=password),
                Database=database,
                Ssl=ssl,
                UseOnlySspi=use_only_sspi
            )
        else:
            raise Exception(f"{connector_type.name} connector type not supported")

        return self.__initialize_context(config=config)
