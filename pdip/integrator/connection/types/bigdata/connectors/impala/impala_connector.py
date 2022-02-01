import pyodbc

from ...base.big_data_connector import BigDataConnector
from .....domain.authentication.mechanism import MechanismTypes
from .....domain.bigdata import BigDataConnectionConfiguration


class ImpalaConnector(BigDataConnector):
    def __init__(self, config: BigDataConnectionConfiguration):
        self.config: BigDataConnectionConfiguration = config
        if self.config.ConnectionString is not None and self.config.ConnectionString != '' and not self.config.ConnectionString.isspace():
            self.connection_string = self.config.ConnectionString
        else:
            if self.config.Driver is None or self.config.Driver == '':
                self.config.Driver = self.find_driver_name()
            self.connection_string = f'Driver={self.config.Driver};Host={self.config.Server.Host};Port={self.config.Server.Port};'
            if self.config.Database is not None and self.config.Database != '':
                self.connection_string += f'Database={self.config.Database};'
            if self.config.AuthenticationMechanismType == MechanismTypes.NoAuthentication:
                pass
            elif self.config.AuthenticationMechanismType == MechanismTypes.Kerberos:
                self.connection_string += f'AuthMech=1;KrbRealm={self.config.KerberosAuthentication.KrbRealm};KrbFQDN={self.config.KerberosAuthentication.KrbFqdn};KrbServiceName={self.config.KerberosAuthentication.KrbServiceName};'
            elif self.config.AuthenticationMechanismType == MechanismTypes.UserName:
                self.connection_string += f'AuthMech=2;UID={self.config.BasicAuthentication.User};'
            elif self.config.AuthenticationMechanismType == MechanismTypes.UserNamePassword:
                self.connection_string += f'AuthMech=3;UID={self.config.BasicAuthentication.User};PWD={self.config.BasicAuthentication.Password};'
            if self.config.UseOnlySspi:
                self.connection_string += f'UseOnlySSPI=1;'
            if self.config.Ssl:
                self.connection_string += f'SSL=1;'

        self.connection = None
        self.cursor = None

    def connect(self):
        self.connection = pyodbc.connect(self.connection_string, autocommit=True)
        self.cursor = self.connection.cursor()

    def disconnect(self):
        try:
            if self.cursor is not None:
                self.cursor.close()

            if self.connection is not None:
                self.connection.close()
        except Exception:
            pass

    def find_driver_name(self):
        drivers = pyodbc.drivers()
        driver_name = None
        driver_names = [x for x in drivers if 'Impala' in x or 'impala' in x]
        if driver_names:
            driver_name = list(reversed(driver_names))[0]
        return driver_name

    def get_connection(self):
        return self.connection

    def execute_many(self, query, data):
        self.cursor.fast_executemany = True
        try:
            self.cursor.executemany(query, data)
            self.connection.commit()
            return self.cursor.rowcount
        except Exception as error:
            try:
                self.connection.rollback()
                self.cursor.fast_executemany = False
                self.cursor.executemany(query, data)
                self.connection.commit()
                return self.cursor.rowcount
            except Exception as error:
                self.connection.rollback()
                self.cursor.close()
                raise