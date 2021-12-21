# Generate your own mail server in just a couple of lines

## Declarative, idempotent mail server configuration script

`mkhost` makes it easy to setup your own simple mail server, complete with: multiple domains, multiple mailboxes, multiple aliases, mail forwarding to 3rd party addresses, SMTP/POP3/IMAP support, TLS/SSL support (including X.509 certificate management).

Everything you need is a [single configuration file](mkhost/cfg.py). If you ever need to make a change later, don't worry: `mkhost` will take care of carefully patching your existing configuration with the latest changes.

Currently supported:

1. SSL certificates (by [Let's Encrypt](https://letsencrypt.org/))
2. DKIM (by [OpenDKIM](http://www.opendkim.org/))
3. SMTP server ([Postfix](http://www.postfix.org/))
4. IMAP/POP3 server ([Dovecot](https://www.dovecot.org/))

Later:

1. [GNU Mailman](https://www.list.org/)

# Requirements

1. Debian GNU/Linux based operating system (with `apt-get`) (on the mail host)
2. Python3 (on the mail host)

# How to run

1. Edit the [configuration file](mkhost/cfg.py) as needed
2. Transfer the files to the (remote) mail host

   Example:

   ```bash
   find . -name '*.git' -prune -o -type f -print0
     | tar --null --files-from=- -c
     | ssh my-remote-user@my-remote-host tar --one-top-level=mkhost-repo -xvf - -C /home/my-remote-user/
   ```

3. Login to the (remote) mail host and run:

   ```
   mkhost.py
   ```

# TODO

1. Postfix `master.cf` customization
2. opendkim: skip new selector generation if a recent one already exists; check public/private key files and DNS records!
