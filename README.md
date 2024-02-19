# instalily
Laryn Qi

## development setup

using `Python 3.9.7` and `Node v21.6.1`

### backend
1. `cd backend && python3 -m venv env && source env/bin/activate && pip install -r requirements.txt`
2. `python3 scrape.py`
    - this will take >5.5 hours
3. create `.env` and set `OPENAI_API_KEY` to your OpenAI API key & `SERVER_KEY` to anything you want
4. `python3 seed.py`
    - this will take >3 hours
5. `python3 server.py`

### frontend
1. `cd frontend && npm install`
2. update `baseURL` in `src/api/api.js` to be `{LOCALHOST ADDRESS}/api/v1/query`
3. `npm start`
