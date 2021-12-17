drop login pdi;
CREATE LOGIN pdi WITH PASSWORD = 'pdi!123456';
create database test_pdi;
create user test_pdi for login pdi;
CREATE SCHEMA test_pdi