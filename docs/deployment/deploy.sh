#! /bin/bash

cd portals
svn revert settings.py
svn up

cd ..
sed -f sedscript < portals/settings.py > portals/settings.py.new
mv portals/settings.py.new portals/settings.py

kill -15 `cat /tmp/portal.pid`

cd portals
python manage.py runfcgi method=threaded pidfile=/tmp/portal.pid host=127.0.0.1 port=3031

echo "If the following information matches, the deployment is successful."
ps ax | grep 3031 | grep -v grep
cat /tmp/portal.pid

