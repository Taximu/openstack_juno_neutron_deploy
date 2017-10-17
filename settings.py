import os
import pprint
import binascii

class Credentials:
	"""Class for secure credentials."""
	email_address = 'map.reduce@expressmail.dk'
	data = {
		'dbmysqlroot'       : 'rootdb',
		'RABBIT_PASS'       : 'cab5f5cc3dbe930ae825',
		'KEYSTONE_DBPASS'   : 'b8786006ae690fd56793',
		'DEMO_PASS'         : 'admin',
		'ADMIN_TOKEN'       : '99af1a2460bb77a18732',
		'ADMIN_PASS'        : 'cbcbf62597006c441e91',
		'GLANCE_DBPASS'     : '0bafd55f3091233ee758',
		'GLANCE_PASS'       : '92e5bcbfaac261d23f69',
		'NOVA_DBPASS'       : '6b1d80542f4098ed1781',
		'NOVA_PASS'         : '38d822846b8aaeb046fd',
		'DASH_DBPASS'       : '3522e3d7fe115814cdc8',
		'CINDER_DBPASS'     : '40df2a42c6687a4ccc29',
		'CINDER_PASS'       : 'c75b358028de3a913aec',
		'NEUTRON_DBPASS'    : '02160c844a3fa375a824',
		'NEUTRON_PASS'      : 'a4609aa35ac5e37bdb4f',
		'HEAT_DBPASS'       : '164293d12e2033e70d4e',
		'HEAT_PASS'         : '37dcc6e9e66f755acc40',
		'CEILOMETER_DBPASS' : 'c15979290141f581832f',
		'CEILOMETER_PASS'   : '03edd3fc1015262c03ac',
		'TROVE_DBPASS'      : '5c8799191a90e3014019',
		'TROVE_PASS'        : '681d45f94efcd21d88cd'
	}

	def generate(self):
		"""Function to generate passwords."""
		for key, value in self.data.iteritems():
			self.data[key] = binascii.b2a_hex(os.urandom(10))

	def show(self):
		"""Function to show passwords."""
		pprint.pprint(self.data)


class Configurations:
	"""Class to prepare openstack configuration files."""
	controller_config = 'file_path'
	network_config = 'file_path'
	compute_config = 'file_path'
	blck_st_config = 'file_path'
	objt_st_config = 'file_path'

	def __init__(self, configs):
		controller_config = configs['cnf_controller']
		network_config = configs['cnf_network']
		compute_config = configs['cnf_compute']
		blck_st_config = configs['cnf_blck_st']
		objt_st_config = configs['cnf_objt_st']

	def configure_controller_node(controller_config):
		"""Function to configure controller node (basically ip_addresses and passwords)."""
		files = ['my.cnf', 'keystone.conf', 'glance-api.conf', 'glance-registry.conf', 'nova.conf', 
		'neutron.conf', 'ml2_conf.ini', 'cinder.conf', 'proxy-server.conf', 'heat.conf', 'mongodb.conf',
		'ceilometer.conf']
		pass

	def configure_network_node(network_config):
		"""Function to configure network node (basically ip_addresses and passwords)."""
		files = ['dnsmasq-neutron.conf', 'dhcp_agent.ini', 'l3_agent.ini', 'metadata_agent.ini', 'neutron.conf', 'sysctl.conf', 'ml2_conf.ini']
		pass

	def configure_compute_node(compute_config):
		"""Function to configure compute node (basically ip_addresses and passwords)."""
		files = ['nova.conf', 'nova-compute.conf', 'neutron.conf', 'sysctl.conf', 'ml2_conf.ini', 'ceilometer.conf']
		pass

	def configure_block_storage_node(blck_st_config):
		"""Function to configure block storage node (basically ip_addresses and passwords)."""
		files = ['cinder.conf']
		pass

	def configure_object_storage_node(objt_st_config):
		"""Function to configure object storage node (basically ip_addresses and passwords)."""
		files = ['account-server.conf', 'container-server.conf', 'object-server.conf', 'cinder.conf', 'proxy-server.conf']
		pass

	def configure():
		"""Function starts all configuration functions."""
		configure_controller_node(controller_config)
		configure_network_node(network_config)
		configure_compute_node(compute_config)
		configure_block_storage_node(blck_st_config)
		configure_object_storage_node(objt_st_config)

	@roles('controller')
	def update_configs(config_file, searchExp, replaceExp):
		sed(config_file, searchExp, replaceExp)
		run('rm -rf ' + file + '.bak')