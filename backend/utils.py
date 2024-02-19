from dotenv import load_dotenv

load_dotenv()

import os
def rm_dir(path):
    for f in os.listdir(path):
        full_path = f'{path}/{f}'
        if os.path.isdir(full_path):
            rm_dir(full_path)
        else:
            os.remove(full_path)
    os.rmdir(path)

from bs4 import BeautifulSoup
from bs4.element import Comment

# https://stackoverflow.com/questions/1936466/how-to-scrape-only-visible-webpage-text-with-beautifulsoup
def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

def text_from_html(body):
    soup = BeautifulSoup(body, 'html.parser')
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)  
    return u" ".join(t.strip() for t in visible_texts)

def text_from_soup(soup):
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)  
    return u" ".join(t.strip() for t in visible_texts)

DB_DIR = 'db/'

def read_db_dir_keys(db_dir=DB_DIR):
    keys = set()
    for db in os.listdir(PREPEND + db_dir):
        if db == 'unstructured':
            continue
        else:
            splits = db.split('-')
            if len(splits) != 2:
                continue
            ps_number, manufacturer_number = splits
            keys.add(ps_number)
            keys.add(manufacturer_number)
    return keys

def read_db_dir_keys_split(db_dir=DB_DIR):
    ps_numbers = set()
    manufacturer_numbers = set()
    for db in os.listdir(PREPEND + db_dir):
        if db == 'unstructured':
            continue
        else:
            splits = db.split('-')
            if len(splits) != 2:
                continue
            ps_number, manufacturer_number = splits
            ps_numbers.add(ps_number)
            manufacturer_numbers.add(manufacturer_number)
    return ps_numbers, manufacturer_numbers

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
def load_db(db_dir=DB_DIR, ps_number=None, manufacturer_number=None):
    assert not (ps_number is None and manufacturer_number is None), 'must supply either ps_number or manufacturer number'
    dbs = set(os.listdir(PREPEND + db_dir))
    if manufacturer_number is None:
        for db in dbs:
            if db == 'unstructured':
                continue
            else:
                splits = db.split('-')
                if len(splits) != 2:
                    continue
                curr_ps_number, curr_manufacturer_number = splits
                if ps_number == curr_ps_number:
                    manufacturer_number = curr_manufacturer_number
                    break
    elif ps_number is None:
        for db in dbs:
            if db == 'unstructured':
                continue
            else:
                splits = db.split('-')
                if len(splits) != 2:
                    continue
                curr_ps_number, curr_manufacturer_number = splits
                if manufacturer_number == curr_manufacturer_number:
                    ps_number = curr_ps_number
                    break
    path = db_dir + ps_number + '-' + manufacturer_number
    embeddings = OpenAIEmbeddings()
    return FAISS.load_local(PREPEND+path, embeddings)

def load_unstructured(db_dir=DB_DIR):
    embeddings = OpenAIEmbeddings()
    return FAISS.load_local(PREPEND+db_dir+'unstructured', embeddings)

import re
PS_NUMBER_PATT = r'\b([pP][sS]\d{8})\b'
MANUFACTURER_NUMBER_PATT = r'\b[a-zA-Z0-9]{4,11}\b'
CACHE = {}
def _augment_query(query, db_dir=DB_DIR, embed_model="text-embedding-ada-002", k=3):
    db_keys = read_db_dir_keys(db_dir)
    ps_search = set(re.findall(PS_NUMBER_PATT, query)) & db_keys
    ps_augment = ''
    if ps_search:
        for ps in ps_search:
            ps = ps.upper()
            if ps not in CACHE:
                CACHE[ps] = load_db(db_dir=db_dir, ps_number=ps)
            db = CACHE[ps]
            ps_augment += f'CONTEXT FOR {ps}:\n' + "\n\n---\n\n".join(map(lambda item: item.page_content.strip(), db.similarity_search(query, k=k)))
        return ps_augment+"\n\n---CUSTOMER QUERY BELOW---\n\n"+query
    else:
        manufacturer_search = set(re.findall(MANUFACTURER_NUMBER_PATT, query)) & db_keys
        manufacturer_augment = ''
        if manufacturer_search:
            for manufacturer_number in manufacturer_search:
                manufacturer_number = manufacturer_number.upper()
                if manufacturer_number not in CACHE:
                    CACHE[manufacturer_number] = load_db(db_dir=db_dir, manufacturer_number=manufacturer_number)
                db = CACHE[manufacturer_number]
                manufacturer_augment += f'CONTEXT FOR {manufacturer_number}:\n' + "\n\n---\n\n".join(map(lambda item: item.page_content.strip(), db.similarity_search(query, k=k)))
            return manufacturer_augment+"\n\n---CUSTOMER QUERY BELOW---\n\n"+query
        else:
            if 'unstructured' not in CACHE:
                CACHE['unstructured'] = load_unstructured(db_dir=db_dir)
            db = CACHE['unstructured']
            unstructured_augment = f'GENERAL CONTEXT:\n' + "\n\n---\n\n".join(map(lambda item: item.page_content.strip(), db.similarity_search(query, k=k+1)))
            return unstructured_augment + "\n\n---CUSTOMER QUERY BELOW---\n\n"+query

CACHED_PS_NUMBERS = set()
CACHED_MANUFACTURER_NUMBERS = set()
from functools import reduce
def smart_augment(query, history=[], db_dir=DB_DIR, embed_model="text-embedding-ada-002", k=2):
    query_words = query.split(' ')
    history_words = reduce(lambda l1, l2: l1 + l2, [message['content'].split(' ') for message in history if message['role'] == 'user'], [])
    global CACHED_PS_NUMBERS
    global CACHED_MANUFACTURER_NUMBERS
    if not CACHED_PS_NUMBERS:
        CACHED_PS_NUMBERS, CACHED_MANUFACTURER_NUMBERS = read_db_dir_keys_split(db_dir=db_dir)
    ps_numbers = CACHED_PS_NUMBERS
    manufacturer_numbers = CACHED_MANUFACTURER_NUMBERS
    ps_number_matches = set()
    manufacturer_numbers_matches = set()
    for w in query_words:
        w = ''.join([c for c in w if c.isalnum()])
        w = w.upper()
        if w in ps_numbers:
            ps_number_matches.add(w)
        if w in manufacturer_numbers:
            manufacturer_numbers_matches.add(w)
    if ps_number_matches == set() and manufacturer_numbers_matches == set():
        if 'unstructured' not in CACHE:
            CACHE['unstructured'] = load_unstructured(db_dir=db_dir)
        db = CACHE['unstructured']
        unstructured_augment = f'GENERAL CONTEXT:\n' + "\n\n---\n\n".join(map(lambda item: item.page_content.strip(), db.similarity_search(query, k=k+1)))
        # return augment_query(query, db_dir=db_dir, embed_model=embed_model, k=k)
    else:
        unstructured_augment = ''
    for w in history_words:
        w = ''.join([c for c in w if c.isalnum()])
        w = w.upper()
        if w in ps_numbers:
            ps_number_matches.add(w)
        if w in manufacturer_numbers:
            manufacturer_numbers_matches.add(w)
    ps_augment = ''
    for ps in ps_number_matches:
        if ps not in CACHE:
            CACHE[ps] = load_db(db_dir=db_dir, ps_number=ps)
        db = CACHE[ps]
        ps_augment += f'CONTEXT FOR {ps}:\n' + "\n---\n".join(map(lambda item: item.page_content.strip(), db.similarity_search(query, k=k)))
    manufacturer_augment = ''
    for manufacturer_number in manufacturer_numbers_matches:
        manufacturer_number = manufacturer_number.upper()
        if manufacturer_number not in CACHE:
            CACHE[manufacturer_number] = load_db(db_dir=db_dir, manufacturer_number=manufacturer_number)
        db = CACHE[manufacturer_number]
        manufacturer_augment += f'CONTEXT FOR {manufacturer_number}:\n' + "\n---\n".join(map(lambda item: item.page_content.strip(), db.similarity_search(query, k=k)))
    return ps_augment + '\n\n' + manufacturer_augment + '\n\n' + unstructured_augment + "\n\n---CUSTOMER QUERY BELOW---\n\n"+query

import sys
PREPEND = sys.path[0] + '/'
if __name__ == '__main__':
    PREPEND = ''
    # augmented = augment_query('The ice maker on my Whirlpool fridge is not working. How can I fix it?')
    # ps, manu = read_db_dir_keys_split()
    # print(ps)
    # print(manu)
    # exit()
    # augmented = augment_query('Tell me more')
    # augmented = smart_augment('tell me more')
    history = [
        {"role": "assistant", "content": 'asdfsdaf'},
        {"role": "user", "content": 'How can I install part number PS11752778?'},
    ]
    augmented = smart_augment('tell me more', history=history)
    print(augmented, len(augmented))
    PRIMER = f"""You are Q&A bot for an e-commerce site. You are a highly intelligent system that answers
    customer questions about various products.

    If the customer is asking a product-specific question, you will first be provided with information about the product
    the customer is inquiring about including the product description, reviews, general troubleshooting advice, 
    repair stories from customers, and popular questions from other customers and their corresponding answers
    scraped from the site. Use this information to answer the customer's question about this product.

    If the customer is asking a general question, you will first be provided with general context that is semantically similar to their question such as troubleshooting advice, repair stories from customers, and popular questions from other customers and their corresponding answers. Use this information to answer the customer's general question.

    If the information can not be found in the provided context, you should truthfully say "I don't know".

    If the customer asks a question about something unrelated to the context you are provided, you should say "Sorry, I can only help with product-related questions."
    """
    # from openai import OpenAI
    # client = OpenAI(
    #     api_key=os.environ['OPENAI_API_KEY'],  # this is also the default, it can be omitted
    # )
    # res = client.chat.completions.create(
    #     # model="gpt-3.5-turbo",
    #     model="gpt-4-turbo-preview",
    #     messages=[
    #         {"role": "system", "content": PRIMER},
    #         {"role": "user", "content": augmented}
    #     ]
    # )

    # print(res.choices[0].message.content)
    # print(augment_query('How can I install part number PS11752778?'))
    # print(load_db(DB_DIR, ps_number='PS223619'))
    # print(load_db(DB_DIR, manufacturer_number='EDR4RXD1'))
