![Alt text](http://occi-wg.org/wp-content/uploads/2010/12/openstack_slide.png)
##What is the purpose of this repo?
It is an automated installation of Openstack Juno Neutron platform, all the nodes + CephFS as the default filesystem for Block and Device Storages. Automation tool: Fabric.
## Install Ubuntu Server 14.04.1 64-bit
## Setup for development
    cd /root && git clone https://github.com/Taximu/openstack_juno_neutron_deploy.git && sudo apt-get install -y fabric
## Setup for deploy/testing
    ssh ubuntu@controller && cd root/openstackdeploy/deploy && fab <openstack_launch_deploy> || fab <function_name>
