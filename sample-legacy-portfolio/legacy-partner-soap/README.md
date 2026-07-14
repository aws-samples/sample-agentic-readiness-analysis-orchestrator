# Partner Integration Service (SOAP)

Legacy SOAP web service that partners call to submit purchase orders. Built
in 2009 on JAX-WS with Java 6, deployed as a WAR on JBoss 5, backed by
Oracle 11g. Contract defined by a hand-maintained WSDL.

## Architecture
- **Runtime**: JBoss AS 5.1 on RHEL 6, Java 6
- **Protocol**: SOAP 1.1 over HTTP, JAX-WS (RPC/encoded style)
- **Contract**: Hand-edited WSDL + XSDs
- **Database**: Oracle 11g
- **Security**: WS-Security username token, password sent in plaintext
- **Build**: Ant, with wsgen/wsimport run by hand

## Known Issues
- JBoss AS 5.1 and Java 6 are long out of support
- RPC/encoded SOAP style is deprecated and not WS-I compliant
- WS-Security PasswordText (plaintext) over plain HTTP
- WSDL maintained by hand; drifts from the implementation
- XML parsing has no protection against XXE / billion-laughs
- Partner credentials stored in a flat properties file
- No tests; partner onboarding is a manual SOAP-UI session
