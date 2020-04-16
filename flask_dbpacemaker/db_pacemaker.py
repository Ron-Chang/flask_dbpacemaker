import os, sys, inspect, importlib, random
from datetime import datetime, timedelta
from flask_apscheduler import APScheduler


class DBPacemaker:
    """
    Purpose: Keep multi-database awake during a long term crawler assignment.
    目的: 保持（複數）資料庫連線，當爬蟲進行長時間睡眠時。
    Based on flask-sqlalchemy and Flask-APScheduler
    """
    @staticmethod
    def _get_now():
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]

    @classmethod
    def _get_models_list(cls, modules):
        models = list()
        now = cls._get_now()
        for module in modules:
            try:
                importlib.import_module(module)
                models.append(sys.modules[module])
            except Exception as e:
                print(f'[{now}] [{"ERROR":7}🚨] [ * {e}]')
                continue
        return models

    @staticmethod
    def _get_db_binds(config):
        db_binds = getattr(config, 'SQLALCHEMY_BINDS', dict())
        return set(db_binds.keys()) if db_binds else dict()

    @staticmethod
    def _is_table(obj, db_binds):
        if not obj.__class__.__name__ is 'DefaultMeta':
            return False
        if not obj.__bind_key__ in db_binds:
            return False
        return True

    @classmethod
    def _get_all_tables_by_db(cls, db_binds, models_list):
        db_tables = dict()
        for models in models_list:
            for name, obj in inspect.getmembers(models):
                if not cls._is_table(obj=obj, db_binds=db_binds):
                    continue
                if obj.__bind_key__ not in db_tables:
                    db_tables.update({obj.__bind_key__: list()})
                db_tables[obj.__bind_key__].append(obj)
        return db_tables

    @staticmethod
    def _random_pick(tables):
        return tables[random.randint(0, len(tables) - 1)]

    @classmethod
    def _get_random_tables(cls, db_binds, models_list):
        tables_by_db = cls._get_all_tables_by_db(db_binds, models_list)
        if not tables_by_db:
            return None
        return {db: cls._random_pick(tables) for db, tables in tables_by_db.items()}

    @classmethod
    def _poke(cls, db, table, display):
        table.query.first()
        if display is False:
            return
        now = cls._get_now()
        print(f'[{now}] [{"POKE":7}👻] [ * {db.upper()} {table.__name__}]')

    @classmethod
    def awake(cls, config, display):
        """
        Proceed every db which is available and random query a table to keep connection.
        對每個資料庫，做一次亂數取表單，透過請求表單第一個物件，保持db連線狀態。

        :params config: flask config
        :type config: <class 'config.Config'>

        :params display: to display activities of every poke
        :type display: bool
        """
        now = cls._get_now()
        db_binds = cls._get_db_binds(config)
        models_path_list = getattr(config, 'MODELS_PATH_LIST', None)
        if not models_path_list:
            raise Exception(f'[ * = DBPacemaker = "MODELS_PATH_LIST" is empty!]')
        models_list = cls._get_models_list(models_path_list)
        if not models_list:
            raise Exception(f'[ * = DBPacemaker = No available models!]')
        random_tables = cls._get_random_tables(db_binds, models_list)
        if not random_tables:
            raise Exception(f'[ * = DBPacemaker = cannot source any tables!]')
        for db, table in random_tables.items():
            cls._poke(db=db, table=table, display=display)

    @staticmethod
    def _get_path():
        path_list = os.path.splitext(__file__)[0].strip('/').split('/')[-2:]
        path = '.'.join(_ for _ in path_list)
        return path

    @staticmethod
    def _launch_scheduler(app, scheduler, task):
        """
        判斷是否建立 scheduler 實體，插入任務，並啟動 scheduler
        """
        if scheduler:
            scheduler.pause()
            scheduler.add_job(**task)
            scheduler.resume()
        else:
            scheduler = APScheduler()
            scheduler.add_job(**task)
            scheduler.init_app(app)
            scheduler.start()

    @classmethod
    def run(cls, app, config, display=False, scheduler=None):
        """
        Check scheduler for launching and appending awake task.
        檢查載入scheduler，插入喚醒db任務。

        :params app: flask app
        :type app: <class 'flask.app.Flask'>

        :params config: flask config
        :type config: <class 'config.Config'>

        :params display: to display activities of every poke
        :type display: bool

        :params scheduler: flask_apscheduler
        :type scheduler: <class 'flask_apscheduler.scheduler.APScheduler'>
        """
        switch = getattr(config, 'DB_PACEMAKER_SWITCH', True)
        interval = getattr(config, 'POKE_DB_INTERVAL', 60 * 60)

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
        start = (datetime.now() + timedelta(seconds=interval)).strftime('%Y-%m-%d %H:%M:%S')
        display_mode = 'on' if display else 'off'
        status = 'is activated 👻!' if switch else 'is not activated 🚨!'
        print(f'[{now}] [{"INFO":8}] [ * DBPacemaker {status}]')
        if switch:
            print(f'[{now}] [{"INFO":8}] [ * Display mode: {display_mode}]')
            print(f'[{now}] [{"INFO":8}] [ * Start at {start}]')
            task = {
                'id': 'keep_db_connection',
                'func': f'{cls._get_path()}:DBPacemaker.awake',
                'kwargs': {'config': config, 'display': display},
                'trigger': 'interval',
                'seconds': interval
            }
            cls._launch_scheduler(app=app, scheduler=scheduler, task=task)
