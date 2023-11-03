## 実行方法
ターミナルで2つのプログラムを並べて実行する\
片方のプログラムではカメラで人の出入り検出を行い、検出の際はその情報をredisサーバにpushする。\
もう一方のプログラムではredisサーバ（キューの役割）に保存された変化情報をバックエンドサーバーに送出していく。

カメラ
```bash
$poetry run python3 main.py
```

キューの処理
```bash
$poetry run python3 consume.py
```


## 環境構築方法
```bash
$pyenv local $(printf '%s' $(<.python-version))
$bash setup.sh

$sudo apt install redis-server
$sudo systemctl restart redis.service
```