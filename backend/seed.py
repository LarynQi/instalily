import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from tqdm import tqdm
from functools import reduce
import tiktoken
import os
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

DB_DIR = 'db/'

def save_dbs(DB_LOOKUP):
    reverse = {}
    for k, v in DB_LOOKUP.items():
        if v in reverse:
            reverse[v].append(k)
        else:
            reverse[v] = [k]
    for k, v in reverse.items():
        k.save_local(DB_DIR+'-'.join(v))

def seed():
    df_structured = pd.read_csv('../scraper/structured_data.csv', keep_default_na=False)
    DB_LOOKUP = populate_FAISS(df_structured)
    if os.path.isdir(DB_DIR):
        rm_dir(DB_DIR)
    os.mkdir(DB_DIR)
    save_dbs(DB_LOOKUP)

if __name__ == '__main__':
    seed()
