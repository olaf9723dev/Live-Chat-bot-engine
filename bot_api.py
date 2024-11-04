from flask import Flask, request, jsonify
from botengine.custom_train import CustomTrain
from botengine.site_train import SiteTrain
from botengine.bot import BotAnswer

app = Flask(__name__)
# API for train custom data
@app.route('/custom_train', methods=['POST'])
def custom_train():
    data = request.json
    # Use LangChain to process the data
    custom_id = data['custom_id']

    custom_train_instance = CustomTrain(custom_id)
    result = custom_train_instance.start()    

    return jsonify({"result": result})

# API for train site data
@app.route('/site_train', methods=['POST'])
def site_train():
    data = request.json
    # Use LangChain to process the data
    site_train_instance = SiteTrain()
    result = site_train_instance.start()

    return jsonify({"result": "result"})

@app.route('/bot_ans', methods=['GET'])
def bot_ans():
    question = request.args.get('question')

    # Return a JSON response
    bot_ans_instance = BotAnswer(question)
    answer = bot_ans_instance.start()

    response = {
        'answer': answer,
    }
    return jsonify(response) 

@app.route('/crawl_site', methods=['GET'])
def crawl_site():
    return ''

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5000)