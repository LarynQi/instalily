import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from utils import *

BASE_URL = 'https://www.partselect.com'
FRIDGE_URL = 'https://www.partselect.com/Refrigerator-Parts.htm'
DISHWASHER_URL = 'https://www.partselect.com/Dishwasher-Parts.htm'

URLS = [
    FRIDGE_URL,
    DISHWASHER_URL
]

OUT = 'data.csv'

def scrape():
    with open(OUT, 'w') as f:
        f.write('item_name,text,url\n')
    for url in tqdm(URLS, position=0, desc='item types', leave=False):
        main_resp = requests.get(url)
        main_soup = BeautifulSoup(main_resp.content, 'html5lib')
        # print(soup.prettify())
        paths = []
        item_names = []
        for pop_item in main_soup.findAll('a', attrs={
            'class': 'nf__part__detail__title'
        }):
            paths.append(pop_item['href'])
            item_names.append(pop_item.span.text)
        for p, name in tqdm(list(zip(paths, item_names)), position=1, desc=f'popular {url.split("/")[-1].split(".")[0]}', leave=False):
            item_url = BASE_URL + p
            item_resp = requests.get(item_url)
            item_text = text_from_html(item_resp.content)
            clean_name = name.replace('"', '""')
            clean_url = item_url.replace('"', '""')
            clean_text = item_text.replace('"', '""')
            with open(OUT, 'a') as f:
                f.write(f'"{clean_name}","{clean_text}","{clean_url}"\n')

if __name__ == '__main__':
    scrape()
