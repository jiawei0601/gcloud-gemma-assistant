from flask import Flask
app = Flask(__name__)
@app.route('/telegram', methods=['POST'])
def telegram_webhook():
    return 'Paused', 200
@app.route('/', methods=['GET'])
def health_check():
    return 'Service Paused', 200
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
