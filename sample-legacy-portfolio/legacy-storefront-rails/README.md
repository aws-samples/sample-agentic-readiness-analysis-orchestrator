# Online Storefront

Legacy customer-facing storefront. Built in 2008 on Ruby on Rails 2.3 with
Ruby 1.8.7, backed by MySQL 5.1, served by Mongrel behind Apache on EC2.

## Architecture
- **Runtime**: Ruby 1.8.7 (EOL), Rails 2.3 (EOL)
- **App Server**: Mongrel cluster behind Apache mod_proxy_balancer
- **Database**: MySQL 5.1 on a separate EC2 instance
- **Payments**: Direct integration with a deprecated gateway SOAP API
- **Assets**: Served from the app, no CDN
- **Deployment**: Capistrano 2 to a fixed set of EC2 hosts

## Known Issues
- Ruby 1.8.7 and Rails 2.3 are long EOL; many CVEs (incl. mass-assignment)
- Gems pinned in environment.rb, not Bundler; some no longer fetchable
- `attr_accessible` not used; mass-assignment vulnerabilities
- Payment gateway credentials in a checked-in YAML file
- Mongrel is unmaintained; no Rack/Puma
- No HTTPS termination configured in the app tier
- Tests are a stale Test::Unit suite that no longer runs
- Sessions stored in the cookie with the secret in source control
