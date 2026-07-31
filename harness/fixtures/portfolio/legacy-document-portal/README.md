# Intranet Document Portal

Legacy intranet portal for sharing policy documents and forms. Built in 2007
with Adobe ColdFusion 8, backed by SQL Server 2005, on a single Windows
EC2 instance. Files stored on a local disk, not S3.

## Architecture
- **Runtime**: Adobe ColdFusion 8 on IIS 7, Windows Server 2008 (EOL)
- **Language**: CFML (ColdFusion Markup Language)
- **Database**: SQL Server 2005 (EOL April 2016)
- **File Storage**: Local D:\docroot\files (no object storage, no backups offsite)
- **Auth**: Application-managed sessions, no SSO
- **Deployment**: Copy .cfm files over the network share to wwwroot

## Known Issues
- ColdFusion 8 is unsupported and has multiple critical CVEs
- SQL Server 2005 long out of support
- `<cfquery>` blocks build SQL by string concatenation
- Uploaded files written to local disk with original filenames (path traversal)
- No HTTPS; runs HTTP only on the internal network
- Session fixation possible; no token rotation on login
- Single instance; reboot = downtime, disk loss = data loss
- Datasource credentials configured in CF Administrator, password is "cfadmin"
