# Flask Database Pacemaker


`python_requires>=3.6`
`Flask>=1.0.2`
`Flask-APScheduler>=1.11.0`
`Flask-SQLAlchemy>=2.3.2`

## - How to use

1. Set confing.py
>`DB_PACEMAKER_SWITCH` __is required__
>`MODELS_PATH_LIST` __is required__
>`POKE_DB_INTERVAL` default value has _has been set as one hour.

```python
# for DBPacemaker - 透過定時排程請求DB，保持連線
DB_PACEMAKER_SWITCH = True if os.environ['ENVIRONMENT'] == 'develop' else False
MODELS_PATH_LIST = ['spyder_common.models']
POKE_DB_INTERVAL = 60 * 60
```

2. Import package at `app.py`

```python
from flask_dbpacemaker import DBPacemaker
```

- Append this after you declared `config` and `app`

```python
DBPacemaker.run(app, db=db, config=config)
```

- If you got a exist scheduler, you have to add it like this.
```python
DBPacemaker.run(app, db=db, config=config, display=True, secheduler=secheduler)
```

Note: The job permanent trigger is `'interval'`.

<a href="https://www.buymeacoffee.com/ronchang" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" align="right"></a>
Cheers! 🎉
