# Create your own mail server in just a couple of lines

## Declarative, idempotent mail server configuration script

`mkhost` makes it easy to setup your own simple mail server, complete with: multiple domains, multiple mailboxes, multiple aliases, mail forwarding to 3rd party addresses, SMTP/POP3/IMAP support, TLS/SSL support (including X.509 certificate management). Typical use cases include: small- or medium-sized enterprise, family or household, cheap mail (self-)hosting of multiple domains, webapp prototyping etc.

Everything you need is a [single configuration file](mkhost/cfg.py). If you ever need to make a change later, don't worry: `mkhost` will take care of carefully patching your existing configuration with the latest changes.

## Features

1. TLS/SSL certificates (by [Let's Encrypt](https://letsencrypt.org/))
2. DKIM (by [OpenDKIM](http://www.opendkim.org/))
3. SMTP server ([Postfix](http://www.postfix.org/))
4. IMAP/POP3 server ([Dovecot](https://www.dovecot.org/))
5. batch and interactive modes
6. dry run mode

## Synopsis

```
$ mkhost.py --help
usage: mkhost.py [-h] [--doveconf FILE] [--letsencrypt DIR] [--batch]
                 [--dry-run] [--verbose]

Re-configures this machine according to the hardcoded configuration (cfg.py).

optional arguments:
  -h, --help         show this help message and exit
  --doveconf FILE    Dovecot configuration file; default:
                     /etc/dovecot/dovecot.conf
  --letsencrypt DIR  Let's Encrypt home directory; default: /etc/letsencrypt/
  --batch            batch mode (non-interactive)
  --dry-run          dry run (no change)
  --verbose          verbose processing

This program comes with ABSOLUTELY NO WARRANTY.
```

# Requirements

## Requirements for the target mail host

1. [Debian](https://www.debian.org/) GNU/Linux based operating system (with `apt-get`)
2. Python 3.x

## Requirements for your local machine

None.

# How to run

1. Edit [configuration file](mkhost/cfg.py) as needed
2. Transfer files to the (remote) target mail host

   Example:

   ```bash
   find . -name '*.git' -prune -o -type f -print0
     | tar --null --files-from=- -c
     | ssh my-remote-user@my-remote-host tar --one-top-level=mkhost-repo -xvf - -C /home/my-remote-user/
   ```

3. Login to the (remote) target mail host and run:

   ```
   mkhost.py
   ```

# How to test

Here are some 3rd party services you can use to verify your installation:

1. https://testtls.com/
2. https://ssl-tools.net/
3. https://mxtoolbox.com/
4. https://www.dmarcanalyzer.com/spf/checker/

# Caveats

## Not included

1. [SPF](https://en.wikipedia.org/wiki/Sender_Policy_Framework)
2. [DMARC](https://en.wikipedia.org/wiki/DMARC)
3. web server, webmail, mailing list manager...

You need to configure [SPF](https://en.wikipedia.org/wiki/Sender_Policy_Framework) and [DMARC](https://en.wikipedia.org/wiki/DMARC) in your DNS. This will improve your protection against e-mail spoofing and is recommended, but not required.

This is a basic script which does not include any kind of webmail or mailing list manager. You can install those from [Debian](https://packages.debian.org/stable/mail/).

## Non-admin virtual users cannot change their passwords

User authentication is handled by [Dovecot SASL](https://doc.dovecot.org/admin_manual/sasl/). Virtual user passwords are stored encrypted in a [passwd file](https://doc.dovecot.org/configuration_manual/authentication/passwd_file/). This is a minimalistic user management mechanism which does not require a SQL database or LDAP, but we don't know of a generic way for a non-admin user to change anyone's password.

## Batch mode

For each virtual user, the password is auto-generated on the first run and printed to the [log](https://docs.python.org/3/library/logging.html), so make sure to take a note of it (and to delete the log file, if any).

# Feedback and contributions

You are welcome! Please get in touch.

# TODO

1. [ ] Postfix `master.cf` customization
2. [x] (WON'T FIX) opendkim: skip new selector generation if a recent one already exists; check public/private key files and DNS records!
3. [ ] SSH hardening
4. [ ] intermediary certificate (let's encrypt) missing error (some clients)
5. [x] (WON'T FIX) reverse DNS check
6. [ ] DANE support: https://ssl-tools.net/dane
7. [ ] generate DNS records for SPF
8. [ ] generate DNS records for DMARC
9. [ ] (BEGINNER-FRIENDLY) make virtual user password length configurable
