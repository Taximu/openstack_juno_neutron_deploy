#!/usr/bin/env python
# Description: Fabric module to deploy Openstack Juno (neutron architecture).
# Author: Maxim Gorbunov
# E-mail: map.reduce@expressmail.dk
# Place: Technical University of Dresden
# Year: 2015

import os
import sys
import time
import logging
import settings

from fabric.api import *
from fabric.operations import reboot
from settings import Credentials
from fabric.colors import cyan, green, red
from fabric.context_managers import shell_env
from fabric.contrib.files import append, sed, comment
from fabric.decorators import hosts, parallel, serial

logging.basicConfig(level=logging.ERROR)
para_log = logging.getLogger('paramiko.transport')
para_log.setLevel(logging.ERROR)

env.roledefs = {
    'controller'     : ['lab3060@141.76.44.197'],
    'compute'        : ['ubuntu@192.168.10.2', 'ubuntu@192.168.10.4'],
    'network'        : ['']
}

hosts_to_ping = {
    'controller'  : ['openstack.org', 'compute0', 'compute1'],
    'compute0'    : ['openstack.org', 'controller', 'compute1']
    'compute1'    : ['openstack.org', 'controller', 'compute0']
}

#################################
####                         ####
####    Basic Environment    ####
####                         ####
#################################

@roles('controller')
def prepare_configs():
    """Configures Openstack installation with necessary settings."""
    put("openstack/", "/tmp/openstack")
    credentials = Credentials()
    #credentials.generate()
    configurations = Configurations()
    #configurations.configure()

@roles('controller', 'network', 'compute')
def configure_hosts():
    for role in env.roledefs:
        #print env.roledefs[role]
        if env.host_string in env.roledefs[role]:
            print env.host_string, role
            put('templates/' + role + '/hosts', "/tmp/hosts")
            sudo('mv /tmp/hosts /etc/hosts')
            put('templates/' + role + '/hostname', "/tmp/hostname")
            sudo('mv /tmp/hostname /etc/hostname')
            sudo('service hostname restart')
            put('templates/' + role + '/interfaces.new', "/tmp/interfaces.new")
            sudo('mv /tmp/interfaces.new /etc/network/interfaces')
            with settings(warn_only=True):
                reboot()

@roles('controller', 'compute')
def stop_password_prompts():
    """Suppresses the console's password prompts."""
    with settings(warn_only=True):
        append('/etc/sudoers', '%clustersudo ALL=(ALL) NOPASSWD:ALL', use_sudo=True)
        sudo('groupadd clustersudo')
        sudo('sudo adduser ubuntu clustersudo')

@roles('controller', 'compute')
def verify_network_connectivity():
    """Checks connections between hosts and checks access to the internet."""
    for key, value in hosts_to_ping.iteritems():
        role = ''
        for temp_role in env.roledefs.keys():
            if env.host_string in env.roledefs[temp_role]:
                role = temp_role
                if key == role:
                    for hostname in value:
                        sudo('ping -c 4 ' + hostname)

@roles('compute')
def install_ntp_server():
    """NTP server installation launcher for three nodes."""
    for role in env.roledefs:
        if env.host_string in env.roledefs[role]:
            sudo('apt-get install -y ntp')
            put('../configs/' + role + '/ntp.conf', '/tmp/ntp.conf')
            sudo('mv /tmp/ntp.conf /etc/ntp.conf')
            sudo('rm -rf /var/lib/ntp/ntp.conf.dhcp')
            sudo('nohup service ntp restart >& /dev/null < /dev/null &', pty=False)
            time.sleep(15)

@roles('controller', 'compute')
def verify_ntp_server_installation():
    """Checks ntp server installation."""
    with hide('output'):
        if (env.host_string in env.roledefs['network']) or (env.host_string in env.roledefs['compute']):
            occurence_count = sudo('ntpq -c peers | grep -ci "controller"')
            if occurence_count == 0:
                print(red('[Fail]: Contents in the *remote* column should indicate the hostname of the controller node.'))
                sys.exit()
            else:
                print(green('[Success]: Contents in the *remote* column indicate the hostname of the controller node.'))
        else:
            occurence_count = sudo('ntpq -c peers | grep -Eci "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}"')
            if occurence_count == 0:
                print(red('[Fail]: Contents in the *refid* column should reference IP addresses of upstream servers.'))
                sys.exit()
            else:
                print(green('[Success]: Contents in the *refid* column reference IP addresses of upstream servers.'))
        occurence_count = sudo('ntpq -c assoc | grep -ci "sys.peer"')
        if occurence_count == 0:
            print(red('[Fail]: Contents in the *condition* column should indicate sys.peer.'))
            sys.exit()
        else:
            print(green('[Success]: Contents in the *condition* column indicate sys.peer.'))

@roles('controller', 'compute')
def install_openstack_packages():
    """Installs openstack packages."""
    sudo('apt-get install -y ubuntu-cloud-keyring')
    sudo('echo "deb http://ubuntu-cloud.archive.canonical.com/ubuntu" \
    "trusty-updates/juno main" > /etc/apt/sources.list.d/cloudarchive-juno.list')
    sudo('apt-get update && apt-get dist-upgrade -y')
    with settings(warn_only=True):
        reboot(20)

@roles('controller')
def install_mysql_and_configure():
    """Installs MySQL."""
    with hide('output', 'running'):
        run('sudo echo mysql-server-5.5 mysql-server/root_password password '+ credentials.data['dbmysqlroot'] +' | sudo debconf-set-selections')
        run('sudo echo mysql-server-5.5 mysql-server/root_password_again password '+ credentials.data['dbmysqlroot'] +' | sudo debconf-set-selections')
    sudo('apt-get install -y mariadb-server python-mysqldb')
    put('../configs/controller/my.cnf', '/tmp/my.cnf')
    sudo('mv /tmp/my.cnf /etc/mysql/my.cnf')
    sudo('service mysql restart')
    put('mysql_secure_installation.sh', '/tmp/mysql_secure_installation.sh')
    with cd('/tmp'):
        sudo('sh mysql_secure_installation.sh')

@roles('controller')
def install_message_broker():
    """Installs message broker."""
    sudo('apt-get install -y rabbitmq-server')
    with hide('output', 'running'):
        print(cyan('[HIDDEN OUTPUT]: rabbitmqctl change_password guest...'))
        sudo('rabbitmqctl change_password guest ' + credentials.data['RABBIT_PASS'])
        rabbit_version = sudo('rabbitmqctl status | grep rabbit | grep -o "3.*\."')
    if float(rabbit_version[:3]) >= 3.3:
        put('../configs/controller/rabbitmq.config', '/tmp/rabbitmq.config')
        sudo('mv /tmp/rabbitmq.config /etc/rabbitmq/rabbitmq.config')
    sudo('service rabbitmq-server restart')

##################################### EXECUTING STEP 1 #########################################
def set_basic_environment():
    """Executes basic environment setup."""
    prepare_configs()
    execute(stop_password_prompts)
    execute(verify_network_connectivity)
    execute(install_ntp_server)
    execute(verify_ntp_server_installation)
    execute(install_openstack_packages)
    execute(install_mysql_and_configure)
    execute(install_message_broker)

###########################################
####                                   ####
####    Adding the Identity Service    ####
####                                   ####
###########################################

@roles('controller')
def mysql_admin(user, password, command):
    """Runs a mysql command without specifying which database to run it on."""
    run('mysql --default-character-set=utf8 -u%s -p%s -e "%s"' % (user, password, command))

@roles('controller')
def create_keystone_database():
    """Creates keystone database."""
    with hide('output', 'running'):
        print 'Creating keystone database...'
        mysql_admin('root', credentials.data['dbmysqlroot'], 'CREATE DATABASE keystone;')
        mysql_admin('root', credentials.data['dbmysqlroot'], "GRANT ALL PRIVILEGES ON keystone.* TO 'keystone'@'localhost' IDENTIFIED BY '" + credentials.data['KEYSTONE_DBPASS'] + "';")
        mysql_admin('root', credentials.data['dbmysqlroot'], "GRANT ALL PRIVILEGES ON keystone.* TO 'keystone'@'%' IDENTIFIED BY '" + credentials.data['KEYSTONE_DBPASS'] + "';")

@roles('controller')
def set_keystone_components():
    """Sets keystone components."""
    sudo('apt-get install -y keystone python-keystoneclient')
    put('../configs/controller/keystone.conf', '/tmp/keystone.conf')
    sudo('mv /tmp/keystone.conf /etc/keystone/keystone.conf')
    sudo('su -s /bin/sh -c "keystone-manage db_sync" keystone')

@roles('controller')
def finalize_keystone_installation():
    """Finalizes keystone setup."""
    sudo('service keystone restart')
    sudo('rm -f /var/lib/keystone/keystone.db')
    sudo("(crontab -l -u keystone 2>&1 | grep -q token_flush) || \
    echo '@hourly /usr/bin/keystone-manage token_flush >/var/log/keystone/keystone-tokenflush.log 2>&1' \
    >> /var/spool/cron/crontabs/keystone")

@roles('controller')
def configure_identity_service_prerequisites():
    """Configures Identity Service prerequisites."""
    with hide('output', 'running'):
        print(cyan('[HIDDEN OUTPUT]: exporting OS_SERVICE_TOKEN...'))
        run('export OS_SERVICE_TOKEN=' + credentials.data['ADMIN_TOKEN'])
    run('export OS_SERVICE_ENDPOINT=http://controller:35357/v2.0')

@roles('controller')
def create_all_subjects():
    """Creates tenants, users, roles."""
    with settings(warn_only=True):
        with shell_env(OS_SERVICE_TOKEN=credentials.data['ADMIN_TOKEN'], OS_SERVICE_ENDPOINT='http://controller:35357/v2.0'):
            run('keystone tenant-create --name admin --description "Admin Tenant"')
            with hide('output', 'running'):
                print(cyan('[HIDDEN OUTPUT]: keystone user-create --name admin...'))
                run('keystone user-create --name admin --pass ' + credentials.data['ADMIN_PASS'] + ' --email ' + credentials.email_address)
            run('keystone role-create --name admin')
            run('keystone user-role-add --user admin --tenant admin --role admin')
            run('keystone tenant-create --name demo --description "Demo Tenant"')
            with hide('output', 'running'):
                print(cyan('[HIDDEN OUTPUT]: keystone user-create --name demo...'))
                run('keystone user-create --name demo --tenant demo --pass ' + credentials.data['DEMO_PASS'] + ' --email ' + credentials.email_address)
            run('keystone tenant-create --name service --description "Service Tenant"')

@roles('controller')
def create_service_entity_end_point():
    """Creates the service entity and API endpoint."""
    with settings(warn_only=True):
        with shell_env(OS_SERVICE_TOKEN=credentials.data['ADMIN_TOKEN'], OS_SERVICE_ENDPOINT='http://controller:35357/v2.0'):
            run('keystone service-create --name keystone --type identity --description "OpenStack Identity"')
            run("keystone endpoint-create \
            --service-id $(keystone service-list | awk '/ identity / {print $2}') \
            --publicurl http://controller:5000/v2.0 \
            --internalurl http://controller:5000/v2.0 \
            --adminurl http://controller:35357/v2.0 \
            --region regionOne")

@roles('controller')
def verify_identity_service_installation():
    """Checks Identity Service installation."""
    with settings(warn_only=True):
        run('unset OS_SERVICE_TOKEN OS_SERVICE_ENDPOINT')
        with hide('output', 'running'):
            print(cyan('[HIDDEN OUTPUT]: Verifying identity service installation...'))
            run('keystone --os-tenant-name admin --os-username admin --os-password ' + credentials.data['ADMIN_PASS'] + '\
            --os-auth-url http://controller:35357/v2.0 token-get')
            run('keystone --os-tenant-name admin --os-username admin --os-password ' + credentials.data['ADMIN_PASS'] + '\
            --os-auth-url http://controller:35357/v2.0 tenant-list')
            run('keystone --os-tenant-name admin --os-username admin --os-password ' + credentials.data['ADMIN_PASS'] + '\
            --os-auth-url http://controller:35357/v2.0 user-list')
            run('keystone --os-tenant-name admin --os-username admin --os-password ' + credentials.data['ADMIN_PASS'] + '\
            --os-auth-url http://controller:35357/v2.0 role-list')
            run('keystone --os-tenant-name demo --os-username demo --os-password ' + credentials.data['DEMO_PASS'] + '\
            --os-auth-url http://controller:35357/v2.0 token-get')
            with settings(warn_only=True):
                run('keystone --os-tenant-name demo --os-username demo --os-password ' + credentials.data['DEMO_PASS'] + '\
                --os-auth-url http://controller:35357/v2.0 user-list')
            print(green('[Success]: verified.'))

@roles('controller')
def create_openstack_env_scripts():
    """Creates openstack environment scripts."""
    run('echo "export OS_TENANT_NAME=admin" >> admin-openrc.sh')
    run('echo "export OS_USERNAME=admin" >> admin-openrc.sh')
    with hide('output', 'running'):
        print(cyan('[HIDDEN OUTPUT]: echo "export OS_PASSWORD for admin..."'))
        run('echo "export OS_PASSWORD=' + credentials.data['ADMIN_PASS'] + '" >> admin-openrc.sh')
    run('echo "export OS_AUTH_URL=http://controller:35357/v2.0" >> admin-openrc.sh')
    run('echo "export OS_TENANT_NAME=demo"  >> demo-openrc.sh')
    run('echo "export OS_USERNAME=demo"  >> demo-openrc.sh')
    with hide('output', 'running'):
        print(cyan('[HIDDEN OUTPUT]: echo "export OS_PASSWORD for demo..."'))
        run('echo "export OS_PASSWORD=' + credentials.data['DEMO_PASS'] + '" >> demo-openrc.sh')
    run('echo "export OS_AUTH_URL=http://controller:5000/v2.0" >> demo-openrc.sh')

##################################### EXECUTING STEP 2 #########################################
def add_identity_service():
    """Executes Identity Service setup."""
    execute(create_keystone_database)
    execute(set_keystone_components)
    execute(finalize_keystone_installation)
    execute(configure_identity_service_prerequisites)
    execute(create_all_subjects)
    execute(create_service_entity_end_point)
    execute(verify_identity_service_installation)
    execute(create_openstack_env_scripts)

########################################
####                                ####
####    Adding the Image service    ####
####                                ####
########################################

@roles('controller')
def configure_image_service_prerequisites():
    """Configures Image Service prerequisites."""
    mysql_admin('root', credentials.data['dbmysqlroot'], 'CREATE DATABASE glance;')
    mysql_admin('root', credentials.data['dbmysqlroot'], "GRANT ALL PRIVILEGES ON glance.* TO 'glance'@'localhost' IDENTIFIED BY '" + credentials.data['GLANCE_DBPASS'] + "';")
    mysql_admin('root', credentials.data['dbmysqlroot'], "GRANT ALL PRIVILEGES ON glance.* TO 'glance'@'%' IDENTIFIED BY '" + credentials.data['GLANCE_DBPASS'] + "';")
    with shell_env(OS_USERNAME='admin', OS_PASSWORD=credentials.data['ADMIN_PASS'], OS_TENANT_NAME='admin', OS_AUTH_URL='http://controller:35357/v2.0'):
        run('keystone user-create --name glance --pass ' + credentials.data['GLANCE_PASS'])
        run('keystone user-role-add --user glance --tenant service --role admin')
        run('keystone service-create --name glance --type image --description "OpenStack Image Service"')
        run("keystone endpoint-create \
        --service-id $(keystone service-list | awk '/ image / {print $2}') \
        --publicurl http://controller:9292 \
        --internalurl http://controller:9292 \
        --adminurl http://controller:9292 \
        --region regionOne")

@roles('controller')
def set_glance_components():
    """Sets glance components."""
    sudo('apt-get install -y glance python-glanceclient')
    put('../configs/controller/glance-api.conf', '/tmp/glance-api.conf')
    sudo('mv /tmp/glance-api.conf /etc/glance/glance-api.conf')
    put('../configs/controller/glance-registry.conf', '/tmp/glance-registry.conf')
    sudo('mv /tmp/glance-registry.conf /etc/glance/glance-registry.conf')
    sudo('su -s /bin/sh -c "glance-manage db_sync" glance')

@roles('controller')
def finalize_glance_installation():
    """Finalizes glance installation."""
    sudo('service glance-registry restart')
    sudo('service glance-api restart')
    sudo('rm -f /var/lib/glance/glance.sqlite')

@roles('controller')
def verify_image_service_installation():
    """Checks Image Service installation."""
    run('mkdir /tmp/images')
    run('wget -P /tmp/images http://download.cirros-cloud.net/0.3.3/cirros-0.3.3-x86_64-disk.img')
    with shell_env(OS_USERNAME='admin', OS_PASSWORD=credentials.data['ADMIN_PASS'], OS_TENANT_NAME='admin', OS_AUTH_URL='http://controller:35357/v2.0'):
        run('glance image-create --name "cirros-0.3.3-x86_64" --file /tmp/images/cirros-0.3.3-x86_64-disk.img \
        --disk-format qcow2 --container-format bare --is-public True --progress')
        with hide('output'):
            image_count = run('glance image-list | grep -ci "active"')
            if image_count > 0:
                print(green('[Success]: verified.'))
            else:
                print(red('[Fail]: not verified.'))
                sys.exit()
    run('rm -r /tmp/images')

##################################### EXECUTING STEP 3 #########################################
def add_image_service():
    """Executes Image Service setup."""
    execute(configure_image_service_prerequisites)
    execute(set_glance_components)
    execute(finalize_glance_installation)
    execute(verify_image_service_installation)

##########################################
####                                  ####
####    Adding the Compute service    ####
####                                  ####
##########################################

@roles('controller')
def configure_compute_service_prerequisites():
    """Configures Compute Service prerequisites."""
    mysql_admin('root', credentials.data['dbmysqlroot'], 'CREATE DATABASE nova;')
    mysql_admin('root', credentials.data['dbmysqlroot'], "GRANT ALL PRIVILEGES ON nova.* TO 'nova'@'localhost' IDENTIFIED BY '" + credentials.data['NOVA_DBPASS'] + "';")
    mysql_admin('root', credentials.data['dbmysqlroot'], "GRANT ALL PRIVILEGES ON nova.* TO 'nova'@'%' IDENTIFIED BY '" + credentials.data['NOVA_DBPASS'] + "';")
    with shell_env(OS_USERNAME='admin', OS_PASSWORD=credentials.data['ADMIN_PASS'], OS_TENANT_NAME='admin', OS_AUTH_URL='http://controller:35357/v2.0'):
        run('keystone user-create --name nova --pass ' + credentials.data['NOVA_PASS'])
        run('keystone user-role-add --user nova --tenant service --role admin')
        run('keystone service-create --name nova --type compute --description "OpenStack Compute"')
        run("keystone endpoint-create \
        --service-id $(keystone service-list | awk '/ compute / {print $2}') \
        --publicurl http://controller:8774/v2/%\(tenant_id\)s \
        --internalurl http://controller:8774/v2/%\(tenant_id\)s \
        --adminurl http://controller:8774/v2/%\(tenant_id\)s \
        --region regionOne")

@roles('controller')
def set_nova_components():
    """Sets nova components."""
    sudo('apt-get install -y nova-api nova-cert nova-conductor nova-consoleauth nova-novncproxy nova-scheduler python-novaclient')
    put('../configs/controller/nova.conf', '/tmp/nova.conf')
    sudo('mv /tmp/nova.conf /etc/nova/nova.conf')
    sudo('su -s /bin/sh -c "nova-manage db sync" nova')

@roles('controller')
def finalize_nova_installation():
    """Finalizes nova installation."""
    sudo('service nova-api restart')
    sudo('service nova-cert restart')
    sudo('service nova-consoleauth restart')
    sudo('service nova-scheduler restart')
    sudo('service nova-conductor restart')
    sudo('service nova-novncproxy restart')
    sudo('rm -f /var/lib/nova/nova.sqlite')

@roles('compute')
def configure_compute_node():
    """Configures compute node."""
    sudo('apt-get install -y nova-compute sysfsutils')
    put('../configs/compute/nova.conf', '/tmp/nova.conf')
    sudo('mv /tmp/nova.conf /etc/nova/nova.conf')
    with hide('output'):
        support_kvm = int(run('egrep -c \'(vmx|svm)\' /proc/cpuinfo'))
        if support_kvm == 0:
                print(red('[Fail]: Compute node does not support hardware acceleration. Start to configure...'))
                put('../configs/compute/nova-compute.conf', '/tmp/nova-compute.conf')
                sudo('mv /tmp/nova-compute.conf /etc/nova/nova-compute.conf')
        else:
            print(green('[Success]: Compute node supports hardware acceleration.'))
    sudo('service nova-compute restart')
    sudo('rm -f /var/lib/nova/nova.sqlite')

@roles('controller')
def verify_compute_service_installation():
    """Checks Compute Service installation."""
    with shell_env(OS_USERNAME='admin', OS_PASSWORD=credentials.data['ADMIN_PASS'], OS_TENANT_NAME='admin', OS_AUTH_URL='http://controller:35357/v2.0'):
        run('nova service-list')
        run('nova image-list')

##################################### EXECUTING STEP 4 #########################################
def add_compute_service():
    """Executes Compute Service setup."""
    execute(configure_compute_service_prerequisites)
    execute(set_nova_components)
    execute(finalize_nova_installation)
    execute(configure_compute_node)
    execute(verify_compute_service_installation)

###############################################
####                                       ####
####    Adding the Networking component    ####
####                                       ####
###############################################

@roles('controller')
def configure_controller_node_networking():
    """Configures controller node networking."""
    put('../configs/controller/nova.conf', '/tmp/nova.conf')
    sudo('mv /tmp/nova.conf /etc/nova/nova.conf')
    sudo('service nova-api restart')
    sudo('service nova-scheduler restart')
    sudo('service nova-conductor restart')

@roles('compute')
def configure_compute_node_networking():
    """Configures compute node networking."""
    sudo('apt-get install -y nova-network nova-api-metadata')
    put('../configs/compute/nova.conf', '/tmp/nova.conf')
    sudo('mv /tmp/nova.conf /etc/nova/nova.conf')
    sudo('service nova-network restart')
    sudo('service nova-api-metadata restart')

##################################### EXECUTING STEP 5 #########################################
def add_networking_component():
    """Executes network setup."""
    execute(configure_controller_node_networking)
    execute(configure_compute_node_networking)

###############################################
####                                       ####
####            Openstack Deploy           ####
####                                       ####
###############################################

def openstackdeploy():
    """Launches the deployment of openstack."""
    execute(set_basic_environment)
    execute(add_identity_service)
    execute(add_image_service)
    execute(add_compute_service)
    execute(add_networking_component)


















###############################################
####                                       ####
####            Openstack Remove           ####
####                                       ####
###############################################

def remove_openstack_from_controller_node():
    """Removes openstack services from controller node."""
    sudo('apt-get purge -y ntp')
    sudo('apt-get purge -y ubuntu-cloud-keyring')
    sudo('apt-get purge -y mariadb-server python-mysqldb')
    sudo('apt-get purge -y rabbitmq-server')
    sudo('apt-get purge -y keystone python-keystoneclient')
    with cd('~'):
        run('rm -rf admin-openrc.sh demo-openrc.sh')
    sudo('apt-get purge -y glance python-glanceclient')
    sudo('apt-get purge -y nova-api nova-cert nova-conductor nova-consoleauth \
    nova-novncproxy nova-scheduler python-novaclient')
    sudo('apt-get purge -y neutron-server neutron-plugin-ml2 python-neutronclient')
    sudo('apt-get purge -y openstack-dashboard apache2 libapache2-mod-wsgi memcached python-memcache')
    sudo('apt-get autoremove -y')
    sudo('rm -rf /etc/apt/sources.list.d/cloudarchive-juno.list /etc/apt/sources.list.d/cloudarchive-juno.list.save') 

@roles('network')
def remove_openstack_from_network_node():
    """Removes openstack services from network node."""
    sudo('apt-get purge -y ntp')
    sudo('apt-get purge -y ubuntu-cloud-keyring')
    sudo('apt-get purge -y neutron-plugin-ml2 neutron-plugin-openvswitch-agent \
    neutron-l3-agent neutron-dhcp-agent')
    sudo('apt-get autoremove -y')
    sudo('rm -rf /etc/apt/sources.list.d/cloudarchive-juno.list /etc/apt/sources.list.d/cloudarchive-juno.list.save')

@roles('compute')
def remove_openstack_from_compute_node():
    """Removes openstack services from compute node."""
    sudo('apt-get purge -y ntp')
    sudo('apt-get purge -y ubuntu-cloud-keyring')
    sudo('apt-get purge -y nova-compute sysfsutils')
    sudo('apt-get purge -y nova-network nova-api-metadata')
    sudo('apt-get purge -y neutron-plugin-ml2 neutron-plugin-openvswitch-agent')
    sudo('apt-get autoremove -y')
    sudo('rm -rf /etc/apt/sources.list.d/cloudarchive-juno.list /etc/apt/sources.list.d/cloudarchive-juno.list.save')

def openstack_purge():
    """Launches the openstack removing process."""
    execute(remove_openstack_from_controller_node)
    execute(remove_openstack_from_network_node)
    execute(remove_openstack_from_compute_node)