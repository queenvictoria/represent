#Represent Govhack 2012 project#

##Installation##

Requires Python 2.6+ and the pypi packages from require.txt. OpenShift uses Python 2.6 so anything over that you should check your version specificity. 

These notes are written from memory. Please correct inaccuracies. See trouble shooting section if you hit a snag.

###OS X###

1. Install brew
    https://github.com/mxcl/homebrew/wiki/installation

###Ubuntu###

1. `$ sudo apt-get install python2.6 python2.6-dev python-setuptools`

###OS X / Ubuntu###

1. `$ sudo easy_install pip`
1. `$ pip install virtualenv virtualenvwrapper`
1. Install virtualenv and virtualenvwrapper. Configure your .profile as the installation instructions for virtualenvwrapper suggest.
    http://www.doughellmann.com/projects/virtualenvwrapper/
    http://www.doughellmann.com/docs/virtualenvwrapper/
1. `$ mkvirtualenv represent`
	OR `mkvirtualenv -a [/path/to/project]/represent -r [/path/to/project]/represent/require.txt represent`
1. `$ workon represent`
1. `$ cdproject`
1. `$ pip install -r require.txt`
	You only need to do this if you haven't run the full `mkvirtualenv` command above

####Trouble shooting####

1. Ensure that both `mysql` and `libmysqlclient-dev` are installed
	`sudo apt-get install mysql libmysqlclient-dev`
	OR `sudo apt-get install libmysqlclient-dev` if you already have MySQL installed

##Usage##

###hansard-getter###

Currently there are no settings. It will pull House of Reps Parliament #43. You can alter main.py to change this.

Cancelling a scrape leaves a settings.pickle file behind. This allows you to resume the scrape later. To start a new scrape delete this file.

1. `$ cd hansard-getter`
1. `$ python main.py`

###hansard-parser###

Currently there are no settings. It is hardwired to parse local files in the data directory. It probably doesn't do this recursively--you should check.

1. Create a local MySQL database.
1. `$ cd hansard-parser`
1. `$ cp local_settings.py.example local_settings.py`
1. Configure your database settings in settings.conf (currently mysql on localhost only).
1. `$ python main.py`

###Sample queries###

Select all speeches by the ALP

`SELECT * FROM speech WHERE party = "ALP"`