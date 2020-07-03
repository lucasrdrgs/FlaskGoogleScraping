import re
import os, sys
import subprocess
import requests
import urllib.parse
import json
import bs4
from bs4 import BeautifulSoup as BSoup

GOOGLE = 'https://google.com/search?'
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:65.0) Gecko/20100101 Firefox/65.0'
HEADERS = {'User-Agent': USER_AGENT}

"""
Tags from which we will extract text to
serve as the page's content.
"""
CONTENT_TAGS = [
	'p',
]

"""
These tags will be excluded from parsing,
therefore none of its children or inner text
will be considered content.
"""
EXCLUDE_TAGS = [
	'header',
	'footer',
	'ul',
	'li',
]

"""
Minimum number of whitespaces for some piece
of text to be considered content.
"""
WHITESPACE_TRESHOLD = 15

"""
Maximum number of non-content tags between
two valid content tags.
"""

"""
These enumerators will specify what sources
to look for (all sources or only news sources)
and the time of publication.
"""
class Search:
	ALL = ''
	NEWS = 'nws'
	API_DICT = {'all': ALL, 'news': NEWS}
class Date:
	ANY = ''
	HOUR = 'h'
	DAY = 'd'
	WEEK = 'w'
	MONTH = 'm'
	YEAR = 'y'
class Lang:
	ANY = ''
	EN = 'en'
	PT = 'pt'

class SearchResult(object):
	"""
	Constructor.

	Parameters:
	url: page's URL.
	title: page's <title> text.
	description: Google Search's description of the page.
	author (if any): who created the page.

	Returns: SearchResult object.
	"""
	def __init__(self, url, title, description, author = None):
		self.URL = url
		self.Title = title
		self.Description = description
		self.Author = author
		# Images: list of tuples containing the caption
		# and URL of each image in page.
		self.Images = []
		# Content: page's relevant content.
		self.Content = None

	"""
	Stringify a SearchResult object.

	Returns: string.
	"""
	def __str__(self):
		content = self.Content
		if self.Content is not None:
			content = self.Content[:197]
			if self.Content.length >= 197: ctt += '...'
		s = self.Title + '\n'
		if self.Author is not None:
			s += 'By: ' + self.Author + '\n'
		s += 'Description: ' + self.Description + '\n'
		s += 'Content: ' + content
		return s

	"""
	Dictify a SearchResult object.

	Returns: dict.
	"""
	def to_dict(self):
		d = {}
		d['url'] = self.URL
		d['title'] = self.Title
		d['description'] = self.Description
		d['author'] = self.Author
		d['Images'] = []
		for img in self.Images:
			d['Images'].append({
				'caption': img[0],
				'url': img[1],
			})
		d['Content'] = self.Content
		return d

"""
Use Google's closed source image fingerprint algorithm
to encode an image to be used in Google Search by Image.

Parameters:
image: path to your image.

Returns: encoded image string.

PS: requires cURL.
"""
def encode_image(image):
	if image is None:
		return image
	cmd = 'curl -s -F "image_url=" -F "image_content=" -F ' + \
		'"filename=" -F "h1=en"  -F "bih=777" -F "biw=777" ' + \
		f'-F "encoded_image=@{image}" ' + \
		'https://www.google.com/searchbyimage/upload'
	stdout, stderr = subprocess.Popen(
		cmd,
		stdout = subprocess.PIPE, stderr = subprocess.STDOUT,
		shell = True, close_fds = True,
	).communicate()
	stdout = stdout.decode('utf-8')
	if stderr is not None:
		print(
			'Something with cURL went wrong. You may have to'
			'install it if you haven\'t already done so.\n'
			'Error message: ' + stderr.decode('utf-8')
		)
		return None
	encoded_image_url = BSoup(stdout, 'html.parser').find('a')['href']
	parsed = urllib.parse.urlparse(encoded_image_url)
	encoded_image = urllib.parse.parse_qs(parsed.query)['tbs'][0]
	return encoded_image

"""
All-in-one search function. This can search
for images, text, and array of keywords.
You can specify the type of websites to look
for, release date, image (if needed) and number
of pages to fetch.

Parameters:
query: what is going to be searched, text or list of keywords.
sch_type: Search.ALL means any page, Search.NEWS means news only.
sch_date: page's maximum age.
image: an image path to Search by Image. None means regular search.
fetch_n: number of pages to fetch.
drop_unavailable: remove pages from results if unable to access.
content_tags: list of tags which could have relevant content.
exclude_tags: remove elements with these tags before fetching content.
ws_treshold: minimum number of whitespaces to consider a text as content.
break_treshold: stop getting content once the whitespace treshold check fails.
start_page: don't mess with this. The code uses it very specifically.

Returns: list of pages fetched.
"""
def _search(query, sch_type = Search.ALL,
		sch_date = Date.ANY, lang = Lang.ANY, image = None,
		fetch_n = 10, drop_unavailable = True,
		content_tags = CONTENT_TAGS,
		exclude_tags = EXCLUDE_TAGS,
		ws_treshold = WHITESPACE_TRESHOLD,
		break_treshold = True,
		start_page = 0):
	if content_tags is None: content_tags = CONTENT_TAGS
	if exclude_tags is None: exclude_tags = EXCLUDE_TAGS
	if lang is None: lang = Lang.ANY
	if image is not None:
		if not os.path.exists(image):
			print('Invalid image path.')
			return []
	if(fetch_n <= 0):
		print('`fetch_n` must be greater than zero.')
		return []
	if(ws_treshold < 0):
		print('`ws_treshold` must be greater or equal to zero.')
		return []
	if sch_date.lower() == 'any': sch_date = Date.ANY
	sch_type = Search.API_DICT[sch_type]
	if lang.lower() == 'any': lang = Lang.ANY
	# If provided a keyword list, join everything and use it as query.
	# Don't worry, it works.
	if isinstance(query, list) or isinstance(query, tuple):
		query = ' '.join(map(str, query))
	encoded_image = encode_image(image)
	g_url = GOOGLE + '&tbs=' + \
			('qdr:' + sch_date if image is None \
			else encoded_image) + '&tbm=' + sch_type + \
			'&q=' + query + '&oq=' + query + '&start=' + \
			str(start_page * 10) + '&lr=' + \
			('lang_' + lang if lang != Lang.ANY else '')

	response = requests.get(g_url, headers = HEADERS)

	if response.status_code != 200:
		print(f'Something went wrong ({response.status_code}). Response:')
		print(response.content)
		return []

	results = []
	soup = BSoup(response.content, 'html.parser')
	# The div whose HTML id attribute is rso holds
	# 10 search results.
	rso = soup.find(id = 'rso')
	rso_classes = {Search.ALL: 'rc', Search.NEWS: 'g'}
	rso_class = rso_classes[sch_type] if image is None else 'g'
	result_tags = rso.find_all('div', class_ = rso_class)
	for tag in result_tags:
		url = None
		title = None
		description = None
		author = None
		if sch_type == Search.NEWS:
			for anchor in tag.find_all('a'):
				if not anchor.find('img'):
					title = anchor.get_text()
					url = anchor['href']
					author = tag.find_all('span')[0].get_text()
					description = tag.find('div', class_ = 'st').get_text()
					break
		else:
			r = tag.find('div', class_ = 'r')
			s = tag.find('div', class_ = 's')
			url = r.find('a')['href']
			title = r.find('a').find('h3').text
			description = s.find('span', class_ = 'st').get_text()
			author = None
		if drop_unavailable:
			if requests.get(url).status_code != 200:
				continue
		res = SearchResult(url, title, description, author)
		results.append(res)
		# Stop retrieving once it reaches fetch_n results.
		if len(results) >= fetch_n: break

	# Now it will treat all pages, removing unneccessary
	# things such as display:none tags. Then we will
	# fetch all image URLs and get the page's content.
	treat(
		results, content_tags, exclude_tags,
		ws_treshold, break_treshold
	)

	# In case there is any empty or inaccessible page...
	if len(results) < fetch_n:
		results += _search(
			query, sch_type, sch_date,
			image, fetch_n - len(results),
			start_page + 1
		)

	return results #dictify(results)

def search(query, sch_type = Search.ALL,
		sch_date = Date.ANY, lang = Lang.ANY, image = None,
		fetch_n = 10, drop_unavailable = True,
		content_tags = CONTENT_TAGS,
		exclude_tags = EXCLUDE_TAGS,
		ws_treshold = WHITESPACE_TRESHOLD,
		break_treshold = True):
	r = _search(query, sch_type, sch_date, lang, image,
			fetch_n, drop_unavailable, content_tags,
			exclude_tags, ws_treshold, break_treshold)
	return dictify(r)

"""
Turn list of SearchResults into a list of dictionaries.

Parameters:
l: list of SearchResults

Returns: SearchResults encoded into dicts inside a list.
"""
def dictify(l):
	ds = []
	for r in l:
		ds.append(r.to_dict())
	return ds

"""
Treat pages in a list, removing hidden content,
fetching all image URLs and content.

Parameters:
pages: list of SearchResult pages to treat.
the rest: defined in search(...).

Returns: list of treated SearchResult pages
"""
def treat(pages, content_tags, exclude_tags,
		ws_treshold, break_treshold):
	for page in pages:
		r = requests.get(page.URL)
		if(r.status_code != 200):
			print(
				'Something went wrong during page treatment.'
				'Skipping. URL: ' + page.URL
			)
			continue

		# Time to parse HTML, removing useless stuff.
		soup = BSoup(r.content, 'html.parser')
		for elem in soup.find_all(text = True):
			if isinstance(elem, bs4.NavigableString):
				continue
			elem_style = elem.style.text.replace(' ', '').lower()
			for line in elem_style.split():
				hidden = re.match(r'^\.(.*?)\{display:none\}', line)
				if hidden or 'display:none' in elem_style:
					elem.decompose()
			if elem.name in exclude_tags:
				elem.decompose()

		# Now it gets the image URLs and descriptions, adding
		# them to their respective SearchResult object.
		for img in soup.find_all('img'):
			alt = img.get('alt')
			src = img.get('src')
			if src != '' and src is not None:
				page.Images.append((alt, src))

		# Then fetch all relevant content.
		content_started = False
		content = ''
		for elem in soup.find_all(content_tags):
			txt = elem.get_text()
			if len(txt.split()) >= ws_treshold or \
			(break_treshold and not content_started):
				content += elem.get_text() + ' '
				content_started = True
			elif content_started and break_treshold:
				content_started = False
				break
		content = content.replace('\r\n', '\n')
		content = re.sub(r'\n\s*\n', r'\n\n', content).strip()
		if soup.title is not None:
			page.Title = soup.title.get_text().replace('\r\n', '\n').replace('\n', ' ').strip()
		page.Content = content
		if page.Content == '':
			pages.remove(page)
	return pages