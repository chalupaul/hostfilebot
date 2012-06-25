vchostbot
=========

Pulls a mega list of VMs from a vCenter and generates a host file from them.

Requirements
===========

**pysphere** Available in pypi.


Usage
=====

Pretty easy. Edit hostfilebot.py and change the credentials that you are using in
vCenter at the top of the file. Then put it in your crontab hourly or something.

I haven't tested this on windows because I don't have the means. It should work
just fine though.

Threading helps the execution speed dramatically. You can bump up the threads 
(one per connection) to make it even faster, but remember vCenter only has 32 
available connections and you probably don't want to push that limit.