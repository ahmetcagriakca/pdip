from injector import inject

from pdip.dependency import IScoped
from pdip.integrator.connection.domain.authentication.basic import BasicAuthentication
from pdip.integrator.connection.domain.authentication.kerberos import KerberosAuthentication
from pdip.integrator.connection.domain.authentication.mechanism import MechanismTypes
from pdip.integrator.connection.domain.bigdata import BigDataConnectionConfiguration
from pdip.integrator.connection.domain.enums import ConnectorTypes, ConnectionTypes
from pdip.integrator.connection.domain.server.base import Server
from .big_data_context import BigDataContext
from .big_data_policy import BigDataPolicy


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
                Server=Server(Host=host, Port=port),
                BasicAuthentication=BasicAuthentication(User=user,
                                                        Password=password),
                KerberosAuthentication=KerberosAuthentication(Principal=user, Password=password),
                Database=database,
                Ssl=ssl,
                UseOnlySspi=use_only_sspi
            )
        else:
            raise Exception(f"{connector_type.name} connector type not supported")

        return self.__initialize_context(config=config)
