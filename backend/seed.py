import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from tqdm import tqdm
from functools import reduce
import tiktoken
import os
import time
from utils import *
from dotenv import load_dotenv

load_dotenv()

# create the length function
def tiktoken_len(text):
    tokenizer_name = tiktoken.encoding_for_model('gpt-4')
    tokenizer = tiktoken.get_encoding(tokenizer_name.name)
    tokens = tokenizer.encode(
        text,
        disallowed_special=()
    )
    return len(tokens)

TEXT_TYPES = {'description', 'reviews', 'troubleshooting', 'repair_stories', 'q_a'}

def populate_FAISS(df_structured):
    DB_LOOKUP = {}
    embeddings = OpenAIEmbeddings(model='text-embedding-ada-002')
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=20,
        length_function=tiktoken_len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    for _, row in tqdm(list(df_structured.iterrows())):
        ps_number, manufacturer_number = row['PS_number'], row['manufacturer_number']
        texts = reduce(lambda l1, l2: l1 + l2, [text_splitter.split_text(row[text_type]) for text_type in TEXT_TYPES])
        db = FAISS.from_texts(texts, embeddings)  
        DB_LOOKUP[ps_number] = db
        DB_LOOKUP[manufacturer_number] = db
    return DB_LOOKUP

def save_dbs(DB_LOOKUP):
    reverse = {}
    for k, v in DB_LOOKUP.items():
        if v in reverse:
            reverse[v].append(k)
        else:
            reverse[v] = [k]
    for k, v in reverse.items():
        k.save_local(DB_DIR+'-'.join(v))
        
def populate_FAISS_and_save(df_structured):
    DB_LOOKUP = {}
    embeddings = OpenAIEmbeddings(model='text-embedding-ada-002')
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=20,
        length_function=tiktoken_len,
        separators=["\n\n", "\n", " ", ""]
    )
    n = df_structured.shape[0]
    for _, row in tqdm(list(df_structured.iterrows())):
        ps_number, manufacturer_number = row['PS_number'], row['manufacturer_number']
        texts = reduce(lambda l1, l2: l1 + l2, [text_splitter.split_text(row[text_type]) for text_type in TEXT_TYPES])
        db = FAISS.from_texts(texts, embeddings)  
        db.save_local(DB_DIR+ps_number+'-'+manufacturer_number)
        DB_LOOKUP[ps_number] = db
        DB_LOOKUP[manufacturer_number] = db
    return DB_LOOKUP

def seed():
    df_structured = pd.read_csv('./structured_data.csv', keep_default_na=False)
    DB_LOOKUP = populate_FAISS_and_save(df_structured)

def seed_unstructured():
    df_unstructured = df_structured = pd.read_csv('./unstructured_data.csv', keep_default_na=False)
    assert os.path.isdir(DB_DIR), f"please seed unstructured data first"
    embeddings = OpenAIEmbeddings(model='text-embedding-ada-002')
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500*2,
        chunk_overlap=20*2,
        length_function=tiktoken_len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    texts = reduce(lambda l1, l2: l1 + l2, [text_splitter.split_text(row['text']) for i, row in tqdm(list(df_unstructured.iterrows()))])
    db = FAISS.from_texts(texts, embeddings)  
    db.save_local(DB_DIR+'unstructured')

if __name__ == '__main__':
    start_time = time.time()
    seed()
    end_time = time.time()
    print(f'structured seed start_time: {start_time}')
    print(f'structured seed end_time: {end_time}')

    start_time = time.time()
    seed_unstructured()
    end_time = time.time()
    print(f'unstructured seed start_time: {start_time}')
    print(f'unstructured seed end_time: {end_time}')
