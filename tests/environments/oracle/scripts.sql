alter session set "_ORACLE_SCRIPT"=true;
drop user pdi ;
create user pdi identified by "pdi!123456" ;
grant create session to pdi;
GRANT CONNECT, RESOURCE, DBA TO pdi;
GRANT UNLIMITED TABLESPACE TO pdi;


CREATE user test_pdi identified by "pdi!123456";
GRANT UNLIMITED TABLESPACE TO test_pdi;