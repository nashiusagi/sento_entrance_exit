from urllib.parse import urlencode
from urllib.request import urlopen, Request
import redis
import json

def send_utilize_status(diff):
    if(diff == '-1' or diff == '1'):
        payload = { 'mens_congestion_degree': diff }
        payload = json.dumps(payload).encode('utf-8')
        request = Request('http://18.179.180.74:3000/api/v1/sentos/1', data=payload, method='PUT')

        with urlopen(request) as response:
            body = response.read()
            print('PUTしたー')

    else:
        raise RuntimeError('invalid argument')

def main():
    r = redis.Redis(host='localhost', port=6379, db=0)

    while(True):
        poped_bytes = r.lpop('queue')
        if(poped_bytes):
            poped_diff = poped_bytes.decode('utf8')
            send_utilize_status(poped_diff)

if __name__ == '__main__':
    main()