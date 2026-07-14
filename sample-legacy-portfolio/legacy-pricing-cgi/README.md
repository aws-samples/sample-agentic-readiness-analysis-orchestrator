# Product Pricing Engine (CGI)

Legacy pricing engine exposed as a compiled C++ CGI binary. Built in 2004,
compiled with GCC 3.x, runs under Apache 1.3 on a single Solaris/EC2 host.
Reads pricing rules from flat config files.

## Architecture
- **Runtime**: Apache 1.3 CGI, compiled C++ binary
- **Language**: C++ (pre-C++11), built with GCC 3.4 and a hand-written Makefile
- **Config**: Flat text rule files in /etc/pricing/
- **Data**: Reads a pipe-delimited product file loaded into memory at startup
- **Deployment**: scp the compiled binary to the server, restart Apache

## Known Issues
- Compiled with a decade-old toolchain; no one can reproduce the build
- Uses unsafe C string functions (strcpy/sprintf) - buffer overflow risk
- No bounds checking on CGI query string parsing
- Pricing rules edited in-place on prod; no source of truth
- Apache 1.3 is ancient and unsupported
- Memory leaks on each request (process recycled by Apache eventually)
- No tests; correctness validated by spot-checking output
