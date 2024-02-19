import requests

server_url = 'https://www.ocf.berkeley.edu/~lqi/instalily-server/'

if __name__ == '__main__':
    try:
        print(requests.get(server_url).content.decode("utf-8"))
    except:
        print('failed')
