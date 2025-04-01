## 事前準備

### 仮想環境
```
$ python3 -m venv env
$ source env/bin/activate
$ pip install -r requirements.txt
```

### API KEY のセット
`.env`を作成
```
SESSION_SECRET=YOUR_API_KEY
OPENAI_API_KEY=YOUR_API_KEY
```

## 実行方法
```
$ python app.py
```