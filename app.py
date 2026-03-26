from flask import Flask, render_template
import fetch_tokens

app = Flask(__name__)

@app.route('/')
def index():
    tokens = fetch_tokens.main()
    return render_template('index.html', tokens=tokens)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
