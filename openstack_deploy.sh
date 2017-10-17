#!/bin/bash
# Author: Maxim Gorbunov
# Description: This an automatic script to deploy Openstack Juno - Neutron architecture.

# Text formatting variables
#$(tput bold)             # Bold
#$(tput setaf number)     # Color
#$(tput sgr0)             # Reset

echo
echo "$(tput setaf 6)Welcome to the Openstack Juno - Neutron architecture installation."
echo "Before it starts the necessary packages will be checked if they are available or not. Please do not interrupt anything.$(tput sgr0)"
sleep 8

echo
echo "$(tput setaf 3)Checking Python Package...$(tput sgr0)"
PYTHON=
PYTHON=$(dpkg -s python | grep version)
if [ -n "$PYTHON" ]
then
  echo "$(tput setaf 2)Python has been already installed.$(tput sgr0)"
else
  echo "$(tput setaf 1)Python is not in your system. It will be installed now.$(tput sgr0)"
  apt-get update
  apt-get install python -y
fi

sleep 2
echo
echo "$(tput setaf 3)Checking Fabric Package...$(tput sgr0)"
FABRIC=
FABRIC=$(fab --version | grep Fabric)
if [ -n "$FABRIC" ]
then
  echo "$(tput setaf 2)Fabric has been already installed.$(tput sgr0)"
else
  echo "$(tput setaf 1)Fabric is not in your system. It will be installed now.$(tput sgr0)"
  apt-get update
  apt-get install fabric -y
fi

sleep 2
INSTALLATION_LOG=/var/log/openstack_installation.log
echo
echo "$(tput setaf 6)Installation will output information to the screen and also to the $(tput bold)"$INSTALLATION_LOG
echo "$(tput sgr0)$(tput setaf 6)The installation process will take some time, machines will do a reboot, so, please grab a mug of coffee and wait for some time. =)$(tput sgr0)"
echo "$(tput setaf 6)Deploying Openstack Juno Neutron..."
echo "Starting in 10 seconds...$(tput sgr0)"
echo 
sleep 10
#fab openstackdeploy | tee $INSTALLATION_LOG

echo
echo "$(tput setaf 2)Installation process has been finished. If there were no stops during the installation then it was successful. 
If there were some, please check the $(tput bold)configurations$(tput sgr0) $(tput setaf 2)and run script again.$(tput sgr0)"
echo