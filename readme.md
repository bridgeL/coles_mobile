# Collect remaining value of data of my coles mobile

this script will run forever and collect the data usage every hour

## how to install

python 3.8 +

```
pip install poetry
poetry install
```


## how to set config

1. open and login https://colesmobile.com.au/pages/dashboard/service/
2. click your mobile plan
3. get your serverid in the url

https://colesmobile.com.au/pages/dashboard/service/ `<server id>`

4. create a file named config.ini and put in your username, password, serverid

```ini
[coles]
username = xxxx
password = xxxx
serverid = xxxx
```

## how to run

```
poetry run python app.py
```
