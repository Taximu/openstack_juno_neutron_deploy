def start():
	"""Function to get list of hostnames and their ipaddresses."""
	with open('roles.inf') as f:
		lines = f.readlines()
		check_input(lines)
		lines.pop(0)
		lines.pop(0)
		import pprint
		pprint.pprint(lines)

def check_input(lines):
	for line in lines:
		words = line.split()
		import re
		re1=words[0]	# Variable Name 1
		re2='(\\s+)'	# White Space 1
		re3='(.)'	# Any Single Character 1
		re4='(\\s+)'	# White Space 2
		re5='((?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))(?![\\d])'	# IPv4 IP Address 1

		rg = re.compile(re1+re2+re3+re4+re5,re.IGNORECASE|re.DOTALL)
		m = rg.search('roles.inf')
		if m:
			var1=m.group(1)
			ws1=m.group(2)
			c1=m.group(3)
			ws2=m.group(4)
			ipaddress1=m.group(5)
			print "("+var1+")"+"("+ws1+")"+"("+c1+")"+"("+ws2+")"+"("+ipaddress1+")"+"\n"
			print "Went pretty well."

if __name__ == '__main__':
	start()