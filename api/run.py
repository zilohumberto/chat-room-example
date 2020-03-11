from flask import Flask, render_template
# from app.cache import CacheGateway

app = Flask(__name__)


@app.route("/")
def template_test():
	# cache = CacheGateway() 
	return render_template(
		'rooms.html', 
		rooms=[], 
	)


if __name__ == '__main__':
    app.run(debug=True)
