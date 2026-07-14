# Sales CRM (Desktop)

Legacy Windows desktop CRM used by the field sales team. Built in 2005 with
Visual Basic 6.0, backed by a Microsoft Access (.mdb) file on a shared
network drive, with a nightly sync job to a SQL Server reporting database.

## Architecture
- **Runtime**: Win32 desktop EXE (VB6 runtime), Windows 10/11 via compat shim
- **Language**: Visual Basic 6.0
- **Database**: Microsoft Access 2003 (.mdb) on a SMB file share
- **Reporting DB**: SQL Server 2012 (sync via a scheduled DTS/SSIS package)
- **Distribution**: EXE copied to each laptop by hand
- **Reports**: Crystal Reports 8.5

## Known Issues
- VB6 IDE and runtime are unsupported by Microsoft
- Access .mdb on a file share corrupts under concurrent writes (~monthly)
- No real multi-user locking; "record locked" errors are common
- ODBC connection string with credentials embedded in the EXE
- Crystal Reports 8.5 runtime no longer installable on new machines
- No installer; deployment is "copy the EXE and the .mdb template"
- File share is a single Windows file server with no failover
- No tests, no build server; compiled on one developer's machine
