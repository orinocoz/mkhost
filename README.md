# Declarative, idempotent mail server configuration script

`mkhost` makes it easy to setup your own mail server, complete with: multiple DNS domains, multiple mailboxes, multiple aliases, mail forwarding to 3rd party e-mail addresses, SMTP/POP3/IMAP support and TLS/SSL support (including X.509 certificate management). Everything you need is a [single configuration file](mkhost/cfg.py). If you ever need to make a change later, don't worry: `mkhost` will take care not to overwrite your existing configuration, but rather it will carefully patch it with the latest changes.

Currently covered are:

1. SSL certificates (by [Let's Encrypt](https://letsencrypt.org/)),
2. DKIM (by [OpenDKIM](http://www.opendkim.org/))
3. SMTP server (by [Postfix](http://www.postfix.org/))
4. IMAP/POP3 server (by [Dovecot](https://www.dovecot.org/))

In progress:

1. [GNU Mailman](https://www.list.org/)

# How to run

1. Edit the [config file](mkhost/cfg.py); this is the only config file you need
2. Transfer the files to the remote host

   Example:

   ```
   find . -name '*.git' -prune -o -type f -print0 | tar --null --files-from=- -c | ssh my-remote-user@my-remote-host tar --one-top-level=mkhost-repo -xvf - -C /home/my-remote-user/
   ```

3. Login to the remote host and run:

   ```
   mkhost.py
   ```

# TODO

1. Postfix `master.cf` customization
