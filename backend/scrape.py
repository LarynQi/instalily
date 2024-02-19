import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import re
import time
from utils import *

BASE_URL = 'https://www.partselect.com'
FRIDGE_URL = 'https://www.partselect.com/Refrigerator-Parts.htm'
DISHWASHER_URL = 'https://www.partselect.com/Dishwasher-Parts.htm'

URLS = [
    FRIDGE_URL,
    DISHWASHER_URL
]

OUT = 'unstructured_data.csv'
STRUCTURED_OUT = 'structured_data.csv'

PS_NUMBER_PATT = r'\b(PS\d{8})\b'

MISSING_TEXT = 'Sorry, this part is No Longer Available at PartSelect.com, which means:'
MISSING_SUB_TEXT = """Sorry, this part is No Longer Available at PartSelect.com, which means: 
    1. The part is no longer sold by the manufacturer.
    2. The manufacturer does not stock any substitute parts to replace this one and therefore, unfortunately, we cannot obtain or recommend a substitution for this part.
    3. We cannot obtain the part through any other means.
"""

SEEN = set()

def scrape(urls=URLS, write=True, write_header=True):
    if write and write_header:
        with open(OUT, 'w') as f:
            f.write('item_name,PS_number,manufacturer,manufacturer_number,text,url\n')
        with open(STRUCTURED_OUT, 'w') as f:
            f.write('PS_number,manufacturer_number,description,reviews,troubleshooting,repair_stories,q_a\n')
    for url in urls:
        SEEN.add(url)
        main_resp = requests.get(url)
        main_soup = BeautifulSoup(main_resp.content, 'html5lib')
        paths = []
        item_names = []
        for pop_item in main_soup.findAll('a', attrs={
            'class': 'nf__part__detail__title'
        }):
            paths.append(pop_item['href'])
            item_names.append(pop_item.span.text)
        
        adjacent_paths = []
        for lst in main_soup.findAll('ul', attrs={
            'class': 'nf__links'
        })[:2]:
            for list_item in lst.findAll('a'):
                adjacent_paths.append(list_item['href'])
        scrape(list(filter(lambda p: p not in SEEN, map(lambda p: BASE_URL + p, adjacent_paths))), write=write, write_header=False)
        print(f'exploring {url}')
        for p, name in zip(paths, item_names):
            item_url = BASE_URL + p
            if item_url in SEEN:
                continue
            else:
                SEEN.add(item_url)
                print(item_url)
            item_resp = requests.get(item_url)
            item_text = text_from_html(item_resp.content)
            if MISSING_TEXT in item_text:
                if write:
                    path_parts = p[1:].split('-')
                    PS_number = path_parts[0].replace('"', '""')
                    manufacturer = path_parts[1].replace('"', '""')
                    manufacturer_number = path_parts[2].replace('"', '""')
                    
                    clean_name = name.replace('"', '""')
                    clean_url = item_url.replace('"', '""')
                    clean_text = item_text.replace('"', '""')
                    clean_product_description = clean_reviews = clean_troubleshooting = clean_stories = clean_qna = MISSING_SUB_TEXT.replace('"', '""')
                    with open(OUT, 'a') as f:
                        f.write(f'"{clean_name}","{PS_number}","{manufacturer}","{manufacturer_number}","{clean_text}","{clean_url}"\n')
                    with open(STRUCTURED_OUT, 'a') as f:
                        f.write(f'"{PS_number}","{manufacturer_number}","{clean_product_description}","{clean_reviews}","{clean_troubleshooting}","{clean_stories}","{clean_qna}"\n')
                continue
            item_soup = BeautifulSoup(item_resp.content, 'html5lib')
            ### PRODUCT DESCRIPTION ###
            clean_product_description = text_from_soup(item_soup.findAll('div', attrs={
                'class': 'expanded mb-4'
            })[0]).replace('"', '""')
            
            ### REVIEWS ###
            # reviews = item_soup.findAll('div', attrs={
            #     'class': 'expanded mb-4'
            # })[1].findAll('div', attrs={
            #     'class': 'pd__cust-review__submitted-review'
            # })
            # if not reviews:
            #     reviews = item_soup.findAll('div', attrs={
            #     'class': 'expanded mb-4'
            # })[2].findAll('div', attrs={
            #     'class': 'pd__cust-review__submitted-review'
            # })
            reviews = item_soup.findAll('div', attrs={
                'class': 'pd__cust-review__submitted-review'
            })
            if not reviews:
                print(f'no reviews for {item_url}')
                clean_reviews = 'N/A'
            else:
                full_reviews = []
                for r in reviews:
                    review_title = r.findAll('div', attrs={
                        'class': 'bold'
                    })[0].text
                    review_content = r.findAll('div', attrs={
                        'class': 'js-searchKeys'
                    })[0].text
                    full_reviews.append(f'{review_title}:\n\n{review_content}\n\n')                
                clean_reviews = "\n\n---\n\n".join(full_reviews).replace('"', '""')
            
            
            ### TROUBLESHOOTING ###
            troubleshooting = text_from_soup(item_soup.findAll('div', attrs={
                # 'class': 'dynamic-height mb-4 expanded'
                'class': 'expanded dynamic-height mb-4'
            })[0])
            clean_troubleshooting = troubleshooting.replace('"', '""')
            
            ### REPAIR STORIES ###
            full_stories = []
            for story in item_soup.findAll('div', attrs={
                'class': 'repair-story'
            }):
                story_title = story.findAll('div', attrs={
                    'class': 'repair-story__title mb-3 mb-lg-4 js-searchKeys'
                })[0].text.strip()
                story_text = story.findAll('div', attrs={
                    'class': 'repair-story__instruction'
                })[0].text.strip()
                full_stories.append(f'{story_title}:\n\n{story_text}\n\n')
            clean_stories = "\n\n---\n\n".join(full_stories).replace('"', '""')
            
            ### Q&A ###
            questions = []
            answers = []
            full_qna = []
            for i, qna in enumerate(item_soup.findAll('div', attrs={
                'class': 'qna__question js-qnaResponse'
            })):
                q, a = qna.findAll('div', attrs={
                    'class': 'js-searchKeys'
                })
                questions.append(q.text)
                answers.append(a.text)
                full_qna.append(f'QUESTION #{i}: {q.text}\nANSWER #{i}: {a.text}\n\n')
            clean_qna = "\n\n---\n\n".join(full_qna).replace('"', '""')
                
            path_parts = p[1:].split('-')
            PS_number = path_parts[0].replace('"', '""')
            manufacturer = path_parts[1].replace('"', '""')
            manufacturer_number = path_parts[2].replace('"', '""')
            
            clean_name = name.replace('"', '""')
            clean_url = item_url.replace('"', '""')
            clean_text = item_text.replace('"', '""')
            if write:
                with open(OUT, 'a') as f:
                    f.write(f'"{clean_name}","{PS_number}","{manufacturer}","{manufacturer_number}","{clean_text}","{clean_url}"\n')
                with open(STRUCTURED_OUT, 'a') as f:
                    f.write(f'"{PS_number}","{manufacturer_number}","{clean_product_description}","{clean_reviews}","{clean_troubleshooting}","{clean_stories}","{clean_qna}"\n')
if __name__ == '__main__':
    start_time = time.time()
    scrape(write=True)
    end_time = time.time()
    print(f'start_time: {start_time}')
    print(f'end_time: {end_time}')
