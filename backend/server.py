def augment_query4(query, DB_LOOKUP, embed_model="text-embedding-ada-002"):
    ps_search = set(re.findall(PS_NUMBER_PATT, query)) & DB_LOOKUP.keys()
    ps_augment = ''
    if ps_search:
        # ps_augment = f"{','.join(ps_search)}:\n"
        for ps in ps_search:
            ps_augment += f'CONTEXT FOR {ps}:\n' + "\n\n---\n\n".join(map(lambda item: item.page_content.strip(), DB_LOOKUP[ps].similarity_search(query, k=5)))
        return ps_augment+"\n\n-----\n\n"+query
    else:
        manufacturer_search = set(re.findall(MANUFACTURER_NUMBER_PATT, query)) & DB_LOOKUP.keys()
        manufacturer_augment = ''
        for manufacturer_number in manufacturer_search:
            manufacturer_augment += f'CONTEXT FOR {manufacturer_number}:\n' + "\n\n---\n\n".join(map(lambda item: item.page_content.strip(), DB_LOOKUP[manufacturer_number].similarity_search(query, k=5)))
        return manufacturer_augment+"\n\n-----\n\n"+query
    
query = "How can I install part number PS11752778?"
# query = "who won the 2010 nba finals?"
# query = "Is this part compatible with my WDT780SAEM1 model?"
# system message to 'prime' the model
primer = f"""You are Q&A bot for an e-commerce site. You are a highly intelligent system that answers
customer questions about various products. You will first be provided with information about the product
the customer is inquiring about including the product description, reviews, general troubleshooting advice, 
repair stories from customers, and popular questions from other customers and their corresponding answers
scraped from the site. Use this information to answer the customer's question about this product.
If the information can not be found in the provided context, you should truthfully say "I don't know".
"""

from dotenv import load_dotenv

load_dotenv()

augmented = augment_query4(query, DB_LOOKUP2)
from openai import OpenAI


client = OpenAI(
  api_key=os.environ['OPENAI_API_KEY'],  # this is also the default, it can be omitted
)
res = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": primer},
        {"role": "user", "content": augmented}
    ]
)
from IPython.display import Markdown

display(Markdown(res.choices[0].message.content))