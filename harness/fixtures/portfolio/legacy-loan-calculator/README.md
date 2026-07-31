# Loan Origination Calculator

Legacy web application for loan officers to price and submit loan applications.
Built in 2010 on Apache Struts 1.3 with Java 5, deployed as a WAR on
WebLogic 10, backed by Oracle 11g.

## Architecture
- **Runtime**: Oracle WebLogic Server 10.3 on Solaris 10, Java 5
- **Framework**: Apache Struts 1.3 (end of life since 2013)
- **Database**: Oracle 11g (EOL)
- **Build**: Apache Ant, dependencies committed as jars in /lib
- **Deployment**: Manual WAR upload via WebLogic admin console

## Known Issues
- Struts 1.x reached end of life in 2013; no security patches
- Java 5 is ancient and unsupported
- WebLogic 10.3 is well past support
- Dependency jars checked into source control, no version manifest
- ActionForms hold mutable shared state; thread-safety bugs under load
- Connection details in a properties file inside the WAR
- No unit tests; "testing" is a shared UAT environment
- Solaris host is the last one in the data center
