import re

def is_number(x):
	if isinstance(x, str):
		n = re.sub('^-', '', x)
		return str.isdigit(n)
	elif isinstance(x, int) or isinstance(x, float):
		return True
	return False