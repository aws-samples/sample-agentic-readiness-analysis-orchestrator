# IT Helpdesk Ticketing

Legacy internal helpdesk ticketing app. Built in 2012 on Django 1.4 with
Python 2.7, backed by PostgreSQL 9.1, served by Apache + mod_wsgi on a
single EC2 instance.

## Architecture
- **Runtime**: Python 2.7 (EOL Jan 2020), Django 1.4 (EOL 2015)
- **Web Server**: Apache 2.2 + mod_wsgi on Ubuntu 12.04 (EOL)
- **Database**: PostgreSQL 9.1 (EOL) on the same EC2 instance
- **Static Files**: Served from local disk, no CDN
- **Email**: SMTP relay to on-prem Exchange
- **Deployment**: git pull on the server + manual apache restart

## Known Issues
- Python 2.7 is end of life; no security updates
- Django 1.4 is many major versions behind; unsupported
- pip requirements pinned to versions no longer on PyPI mirrors
- SECRET_KEY committed to settings.py
- DEBUG = True in production (leaks stack traces)
- DB on the same box as the app; no backups beyond a daily pg_dump cron
- No virtualenv; packages installed system-wide
- No tests beyond a couple of stale unit tests
