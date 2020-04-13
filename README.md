# Flask Database Pacemaker
<a href="https://www.buymeacoffee.com/ronchang" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" align="right"></a>

`python_requires>=3.6`
`Flask>=1.0.2`
`Flask-APScheduler>=1.11.0`
`Flask-SQLAlchemy>=2.3.2`

## - How to use

- Import package at `app.py`
```python
from flask_dbpacemaker import DBPacemaker
```

- Append this after you declare `config` and `app`

```python
DBPacemaker.run(app=app, config=config, interval=60, display=True)
```

- If you already have a exist scheduler, remember add it as parameters.
```python
DBPacemaker.run(app, config, 60, True, secheduler=secheduler)
```

Note: The job permanent trigger is `'interval'`, and interval unit is set as seconds.
