import time
import requests

SERVER_URL = 'https://www.ocf.berkeley.edu/~lqi/instalily-server/'

if __name__ == '__main__':
    while True:
        try:
            print(requests.get(SERVER_URL).content.decode("utf-8"))
        except:
            print('failed')
        time.sleep(3)
