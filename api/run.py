from flask import Flask, render_template
from requests import get
from json import loads

app = Flask(__name__)


@app.route("/")
def home():
	r = get(url="https://randomuser.me/api/?results=1")
	if r.status_code != 200:
		return

	person = loads(r.text)
	return render_template(
		'rooms.html', 
		user=person['results'][0], 
	)


if __name__ == '__main__':
    app.run(debug=True, host='10.218.227.134', port=5000)
