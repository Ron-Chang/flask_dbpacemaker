# Flask Database Pacemaker
```
python_requires>=3.6
Flask>=1.0.2
Flask-APScheduler>=1.11.0
Flask-SQLAlchemy>=2.3.2
```

## - Log

|#|      date|version|
|-|----------|-------|
|1|2020/12/03| v1.2.3|

#### v1.2.3
- Fixed `AttributeError: 'NoneType' object has no attribute 'items'` issue due to mysql connection has been terminated.

## - How to use

#### 1. Add setting into config.py
- `DB_PACEMAKER_SWITCH` __is required__
- `MODELS_PATH_LIST` __is required__
- `POKE_DB_INTERVAL` default: 1 hour.

```python
# for DBPacemaker - 透過定時排程請求DB，保持連線
DB_PACEMAKER_SWITCH = True if os.environ['ENVIRONMENT'] == 'develop' else False
MODELS_PATH_LIST = ['spyder_common.models']
POKE_DB_INTERVAL = 60 * 60
```

#### 2. Establish in `app.py`
>Note: Append this after you declared `config` and `app`

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_dbpacemaker import DBPacemaker  # import package
from config import Config

app = Flask(__name__)
config = Config()
app.config.from_object(config)

db = SQLAlchemy(app)

DBPacemaker.run(app, db=db, config=config)  # setup here
```

- If you've set a scheduler
```python
DBPacemaker.run(app, db=db, config=config, secheduler=your_flask_apscheduler)
```

_Note: The job permanent trigger is `interval`._

If you like my work, please consider buying me a coffee or [PayPal](https://paypal.me/RonDevStudio?locale.x=zh_TW)
Thanks for your support! Cheers! 🎉
<a href="https://www.buymeacoffee.com/ronchang" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" align="right"></a>
