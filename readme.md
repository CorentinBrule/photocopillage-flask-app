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
flask run
```

### celery
only for longtask : server side generation cover images 
```celery -A app.celery  worker --loglevel=INFO```
