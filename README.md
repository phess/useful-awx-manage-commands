# useful-awx-manage-commands
New commands to run as 'awx-manage &lt;command&gt;'

## How to use

### DISCLAIMER

**The utility scripts and commands provided in this repo are not analyzed or approved or vetted in any way by my employer or by the awx engineering team.**

These commands are developed for the Ansible Automation Platform Controller version I work with, mostly version 4.5.* (i.e. AAP 2.4) at this time.
Ansible Automation Platform Controller is a downstream product of the awx project.
So each of the commands here may or may not be compatible with the awx version you are running.

### Download the script

You may choose to clone this repository into your own awx server or you may download individual python scripts directly. Either will work.


### Place the script in the appropriate directory

On AAP Controller 4.5.* you should place the downloaded python script under this directory:
~~~
/var/lib/awx/venv/awx/lib/python3.9/site-packages/awx/main/management/commands/
~~~

For example, the `diff_user_perms.py` file would then be placed at:
~~~
/var/lib/awx/venv/awx/lib/python3.9/site-packages/awx/main/management/commands/diff_user_perms.py
~~~

Remember to change the script file's permissions and ownership and SELinux context as appropriate (using `diff_user_perms.py` as an example):
~~~
# chown root:root /var/lib/awx/venv/awx/lib/python3.9/site-packages/awx/main/management/commands/diff_user_perms.py
# chmod 0644 /var/lib/awx/venv/awx/lib/python3.9/site-packages/awx/main/management/commands/diff_user_perms.py
# command -v restorecon && restorecon -F /var/lib/awx/venv/awx/lib/python3.9/site-packages/awx/main/management/commands/diff_user_perms.py
~~~

### Run the script

If the script has the correct contents and is at the correct location, it will show in the output of:
~~~
# awx-manage --help
~~~

You don't need to confirm it with the command above; you may simply call the command directly:
NOTE: When calling the command you do not include the script filename's `.py` extension.
~~~
# awx-manage diff_user_perms --help
~~~

**NOTE**: Every script available here comes with a useful `--help` section. If you find a script's `--help` section is not helpful, please open an issue against this repository.

Enjoy! :-)
