CREATE LOGIN pdi WITH PASSWORD = 'pdi!123456';
create database pdi;
create user pdi for login pdi;
create table test_integration (Id int, Text Nvarchar(100));
USE pdi;
Grant select on test_integration to pdi