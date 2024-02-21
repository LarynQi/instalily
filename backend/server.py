from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
import time
from utils import *
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
cors = CORS(app)

api_v1_cors_config = {
  "origins": ["https://larynqi.com"],
  "methods": ["OPTIONS", "GET", "POST"],
  "allow_headers": ["Authorization", "Content-Type"]
}

from openai import OpenAI
client = OpenAI(
  api_key=os.environ['OPENAI_API_KEY'],  # this is also the default, it can be omitted
)

PRIMER = f"""You are a friendly Q&A bot for an e-commerce site called PartSelect.com. You are a highly intelligent system that answers customer questions about various products. Your primary function is to provide product information and assist with customer
transactions. It is crucial that you remain focused on this specific use case, avoiding responses to questions outside this scope. If the customer asks a question that is not product-related, you should say "Sorry, I can only help with product-related questions."

If the customer is asking a product-specific question, you will first be provided with information about the product the customer is inquiring about including the product description, reviews, general troubleshooting advice, repair stories from customers, and popular questions from other customers and their corresponding answers scraped from the site. Use this information to answer the customer's question about this product.

If the customer is asking a general product-related question, you will first be provided with general context that is semantically similar to their question such as troubleshooting advice, repair stories from customers, and popular questions from other customers and their corresponding answers. Use this information to answer the customer's general question.

If you are asked about part compatability, pay attention to appliance type. For example, refridgerator parts are not likely to be compatible with dishwasher models. For parts and models that are the same appliance type, consider the manufacturer and provided context.

You can include the SOURCE URL(s) of the pieces of context you used to answer the customer's question if you think the customer would find it valuable.

In addition to the customer's most recent query, you will also be given a history of your conversation with this customer so far. Use this context to resolve ambiguities in the customer's most recent query, if possible. Be specific with your response and try to connect your response to the conversation history thus far.

If you don't have enough information to answer confidently, you should truthfully say "Sorry, I don't know", but try to point the customer toward where they could find the answer. Ensure you aren't responding with any contradictions.

Keep your response concise unless the customer asks you to elaborate or asks for a more verbose response. Don't mention the previous messages and context explicitly unless it's directly relevant to answering the customer's question.

Make sure you are directly answering the customer's latest question. Be specific and reference parts mentioned in the conversation history if it's relevant.

Be friendly!
"""

MODEL = 'gpt-4-turbo-preview'
LOG_FILE = 'log.txt'
ERROR_LOG_FILE = 'error-log.txt'

@app.route('/api/v1/query', methods=['POST'])
@cross_origin(**api_v1_cors_config)
def query():
    q = request.json.get('query')
    history = request.json.get('history')
    server_key = request.json.get('serverKey')
    if server_key.strip() != os.environ['SERVER_KEY']:
        return jsonify({
            'response': 'Wrong key. Refresh the page and resubmit the key.',
            'augmented_query': 'N/A'
        })
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        ip = request.environ['REMOTE_ADDR']
    else:
        ip = request.environ['HTTP_X_FORWARDED_FOR']
    try:
        augmented_q = smart_augment(q, history=history)
        augment, rest = augmented_q.split(AUGMENT_DELIMITER)
        res = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": PRIMER}
            ] + 
            history +
            [
                {"role": "system", "content": augment},
                {"role": "user", "content": user_history(history, k=3) + q}
            ]
        )

        with open(PREPEND + LOG_FILE, 'a') as f:
            f.write(f'{ip}-{round(time.time())}: query={q}, history={str(history)}, response={res.choices[0].message.content}, augmented_query={augmented_q}, user_history={user_history(history, k=3)}\n')
        return jsonify({
            'response': res.choices[0].message.content,
            'augmented_query': augmented_q
        })

    except Exception as e:
        with open(PREPEND + ERROR_LOG_FILE, 'a') as f:
            f.write(f'{ip}-{round(time.time())}: query={q}, history={str(history)}, exception={str(e)}\n')
        return jsonify({
            'response': f'Sorry, a server-side error has occurred. Please try again later.\n{str(e)}',
            'augmented_query': 'N/A'
        })

@app.route('/', methods=['GET'])
def home():
    return f'instalily-server. by Laryn Qi. v4.27 using MODEL={MODEL}'

import sys
PREPEND = sys.path[0] + '/'
if __name__ == '__main__':
    app.run()
