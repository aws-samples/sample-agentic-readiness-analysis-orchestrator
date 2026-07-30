# Payroll Processing System

Legacy biweekly payroll batch system. Built in 2003, runs COBOL batch jobs
against a DB2 database, orchestrated by JCL on a z/OS mainframe with a
thin EC2-hosted file gateway.

## Architecture
- **Runtime**: IBM z/OS mainframe (COBOL batch), EC2 m4.large file gateway
- **Language**: COBOL (Enterprise COBOL 4.2), some JCL
- **Database**: IBM DB2 for z/OS v10 (out of support)
- **Integration**: Nightly FTP of fixed-width files to/from EC2 gateway
- **Scheduling**: CA-7 job scheduler on mainframe
- **Output**: Fixed-width flat files, printed checks via line printer

## Known Issues
- COBOL skills are scarce; original authors retired
- DB2 v10 is end of support (EOS April 2020)
- Fixed-width file formats with no schema/versioning
- Plaintext FTP of SSN and bank account data to the EC2 gateway
- No source control until the files were copied here in 2021
- Hardcoded dataset names and credentials in JCL
- Batch window is shrinking; runs 5-7 hours and sometimes overruns
- No automated tests; changes validated in a shared QA region only
- Tax tables updated by hand each January
