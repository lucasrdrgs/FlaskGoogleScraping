api_params = {
	'api-key': [
		'*',
		'Your API key provided by the developer.'
	],
	'query': [
		'*',
		'What you want to search for. Whitespaces are represented by the character <code>+</code>.'
	],
	'fetch-n': [
		'>0',
		'Number of pages to fetch.',
	],
	'search-type': [
		['all', 'news'],
		'What type of page to look for. For example, <code>news</code> would only fetch news sources.'
	],
	'search-date': [
		['any', 'h', 'd', 'w', 'm', 'y'],
		'Maximum age of pages to fetch.'
	],
	'lang': [
		['any', 'en', 'pt'],
		'Language of the pages to fetch.'
	],
	'drop-unavailable': [
		['true', 'false'],
		'Whether or not to exclude unavailable (inaccessible) pages from final result.'
	],
	'ws-treshold': [
		'>=0',
		'Minimum number of whitespaces to consider a piece of text as content.'
	],
	'break-treshold': [
		['true', 'false'],
		'Whether or not to stop fetching content from page as soon as a whitespace '
		'treshold check fails.'
	],
	'content-tags': [
		['default', '*'],
		'HTML tags to get content from, separated by <code>+</code>. '
		'Default: <code>p</code>.'
	],
	'exclude-tags': [
		['default', '*'],
		'HTML tags to disregard (children included), separated by '
		'<code>+</code>. Default: <code>header+footer+ul+li</code>. '
		'<code>0</code> if none.'
	]
}