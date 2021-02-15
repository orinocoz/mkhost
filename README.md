# How to run

1. Transfer the files to the remote host.

   For example:

   ```
   rsync -vcEthr --delete --exclude=.git --safe-links --progress . USER@HOST:/home/USER/makehost/
   ```

2. Login to the remote host, and run:

   ```
   makehost.py
   ```
