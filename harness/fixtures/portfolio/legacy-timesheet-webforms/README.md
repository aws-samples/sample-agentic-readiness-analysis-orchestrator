# Employee Timesheet (WebForms)

Legacy timesheet entry app for hourly employees. Built in 2006 on ASP.NET
WebForms with .NET Framework 2.0 (VB.NET code-behind), backed by SQL Server
2005, on a single IIS 6 server.

## Architecture
- **Runtime**: ASP.NET WebForms, .NET Framework 2.0, IIS 6, Windows Server 2003
- **Language**: VB.NET (code-behind)
- **Database**: SQL Server 2005
- **State**: ViewState heavy; InProc session
- **Deployment**: Publish from Visual Studio 2005 to a network share

## Known Issues
- .NET Framework 2.0 and Windows Server 2003 are long out of support
- WebForms ViewState bloat makes pages multi-megabyte
- Inline SqlClient queries built by string concatenation
- Connection string with credentials in web.config (not encrypted)
- No HTTPS; forms auth cookie sent in the clear
- IIS 6 / Windows Server 2003 cannot be patched
- No build pipeline; deploy is a manual VS publish
