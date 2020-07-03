import re
import mysql.connector as mysql
from .misc import is_number
from .gscraper import gscraper as google
import requests
import shutil
import os

def number_check(x, param, min):
	if is_number(x):
		x = int(x)
		if x < min:
			return param + ' must be atleast ' + min + '.\n'
	else:
		return param + ' must be an integer.\n'
	return ''

def api(apikey, query, fetch_n, sch_type,
		sch_date, lang, image, drop_unav,
		ws_treshold, break_treshold,
		content_tags, exclude_tags):
	sql_cred = open('/home/vps/www/1/credentials/sql.cred', 'r').read().replace('\n', '')
	sql_cred = sql_cred.split()

	try:
		cnx = mysql.connect(user=sql_cred[0], password=sql_cred[1], host='127.0.0.1', database='gscraper_api')
	except mysql.connector.Error as sql_err:
		return {'error': str(sql_err)}

	cursor = cnx.cursor()

	def close_sql(error = None):
		cnx.commit()
		cursor.close()
		cnx.close()
		if error is not None:
			return {'error': error}

	squery = 'SELECT enabled FROM api_keys WHERE api_key = %s'
	cursor.execute(squery, (apikey,))
	row = cursor.fetchone()
	if row is None: return close_sql('Invalid API key.')
	if not row[0]: return close_sql('API key is disabled.')
	squery = 'UPDATE api_keys SET uses = uses + 1 WHERE api_key = %s'
	cursor.execute(squery, (apikey,))
	close_sql()
	
	err = ''
	err += number_check(fetch_n, 'fetch-n', 1)
	err += number_check(ws_treshold, 'ws-treshold', 0)

	if sch_type.lower() not in ['all', 'news']:
		err += 'Unexpected value for "search-type".\n'

	if sch_date.lower() not in ['any', 'h', 'd', 'w', 'm', 'y']:
		err += 'Unexpected value for "search-date".\n'

	if drop_unav.lower() not in ['true', 'false']:
		err += 'Unexpected value for "drop-unavailable".\n'
	else: drop_unav = {'true': True, 'false': False}[drop_unav.lower()]

	if break_treshold.lower() not in ['true', 'false']:
		err += 'Unexpected value for "break-treshold".\n'
	else: break_treshold = {'true': True, 'false': False}[break_treshold.lower()]

	if content_tags.lower() == 'default':
		content_tags = None
	else: content_tags = content_tags.split('+')

	if exclude_tags == '0' or exclude_tags.lower() == 'none':
		exclude_tags = []
	elif exclude_tags.lower() == 'default':
		exclude_tags = None
	else: exclude_tags = exclude_tags.split('+')

	if not isinstance(image, str) and image is not None:
		err += 'Unexpected value for "image".\n'

	if image is not None:
		try:
			r = requests.get(image)
			assert r.status_code == 200
		except:
			err += 'Image unavailable or inaccessible.\n'

	err = err.strip()

	if err != '':
		return {'error': err}

	img_name = None
	if image is not None:
		img_name = '/home/vps/www/1/tmp/' + image.split('/')[-1]
		r = requests.get(image, stream = True)
		with open(img_name, 'wb') as img_file:
			shutil.copyfileobj(r.raw, img_file)

	fetch_n = int(fetch_n)
	ws_treshold = int(ws_treshold)
	query = query.replace('+', ' ').strip()
	if len(query) == 1: query = 'a'

	what = {
		'results': google.search(query, sch_type, sch_date, lang,
								img_name, fetch_n, drop_unav,
								content_tags, exclude_tags,
								ws_treshold, break_treshold),
		'error': None
	}

	if img_name is not None:
		os.remove(img_name)

	return what
