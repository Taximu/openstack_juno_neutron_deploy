#!/bin/bash
 
apt-get -y install expect
 
SECURE_MYSQL=$(expect -c "

set timeout 10
spawn mysql_secure_installation

expect \"Enter current password for root (enter for none):\"
send \"rootdb\r\"

expect \"Change the root password?\"
send \"n\r\"

expect \"Remove anonymous users?\"
send \"n\r\"

expect \"Disallow root login remotely?\"
send \"n\r\"

expect \"Remove test database and access to it?\"
send \"n\r\"

expect \"Reload privilege tables now?\"
send \"n\r\"

expect eof
")
 
echo "$SECURE_MYSQL"

apt-get -y purge expect