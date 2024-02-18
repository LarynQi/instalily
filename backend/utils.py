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
