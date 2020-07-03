from flask import Flask, render_template as render, jsonify, request
from modules.dicts import api_params
from modules import api_utils

app = Flask(__name__)

@app.route('/')
def index():
	api_url = ''
	for key in api_params:
		api_url += f'<span style="color: #e83e8c;">{key}</span>/'
		if not isinstance(api_params[key][0], list):
			api_params[key][0] = [api_params[key][0]]
	return render('index.html', params = api_params, api_url = api_url)

@app.route(
	'/api/<apikey>/<query>/<fetch_n>/'
	'<sch_type>/<sch_date>/<lang>/'
	'<drop_unav>/<ws_treshold>/<break_treshold>/'
	'<content_tags>/<exclude_tags>/',
	methods = ['GET', 'POST']
)
def api(apikey, query, fetch_n, sch_type,
		sch_date, lang, drop_unav,
		ws_treshold, break_treshold,
		content_tags, exclude_tags):
	image = request.args.get('image')
	return jsonify(api_utils.api(apikey, query, fetch_n, sch_type, sch_date, lang, image, drop_unav, ws_treshold, break_treshold, content_tags, exclude_tags))