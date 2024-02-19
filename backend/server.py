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

If the answer to the customer's question can not be found in the provided context, you should truthfully say "Sorry, I don't know".

Keep your response concise unless the customer asks you to elaborate or asks for a more verbose response. Don't mention the previous messages and context explicitly unless it's directly relevant to answering the customer's question. Don't repeat yourself unnecessarily and don't be redundant (remember that the user can also see your conversation history).

Be friendly!
"""

MODEL = 'gpt-4-turbo-preview'
LOG_FILE = 'log.txt'

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
    try:
        augmented_q = smart_augment(q, history=history)
        res = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": PRIMER}
            ] + 
            history +
            [
                {"role": "user", "content": augmented_q}
            ]
        )

        return jsonify({
            'response': res.choices[0].message.content,
            'augmented_query': augmented_q
        })

    except Exception as e:
        with open(LOG_FILE, 'a') as f:
            f.write(f'{round(time.time())}: query={q}, history={history}, exception={e}\n')
        return jsonify({
            'response': f'Sorry, a server-side error has occurred. Please try again later.\n{e}',
            'augmented_query': 'N/A'
        })

@app.route('/', methods=['GET'])
def home():
    return f'instalily-server. by Laryn Qi. v4.21 using MODEL={MODEL}'

if __name__ == '__main__':
    app.run()
