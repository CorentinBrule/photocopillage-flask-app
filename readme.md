# photocopillage flask app

## install :
```
python -m venv venv/
source venv/bin/active
pip install -r requirements.txt
```

## init :
### flask app

```
source venv/bin/active
python app.py
```

### celery
Only for longtask : server side generation cover images
```
celery -A app.celery  worker --loglevel=INFO
```


## build:
Use flask app as html generator : `curl {url}  > {output_file}.html`

For exemple, to rebuild new static index ("photocopillage-all.html") : `curl localhost:5000/index_generator > static/photocopillage-all.html`
