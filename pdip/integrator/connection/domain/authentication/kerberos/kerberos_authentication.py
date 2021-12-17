from dataclasses import dataclass


@dataclass
class KerberosAuthentication:
    Principal: str = None
    Password: str = None
    KrbRealm: str = None
    KrbFqdn: str = None
    KrbServiceName: str = None
