import os, sys, inspect, importlib, random
from datetime import datetime, timedelta
from flask_apscheduler import APScheduler


class DBPacemaker:
    """
    Keep multi-database awake.
    Based on flask-sqlalchemy and Flask-APScheduler
    """
    @staticmethod
    def _get_models_list(modules):
        models = list()
        for module in modules:
            importlib.import_module(module)
            models.append(sys.modules[module])
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

    @staticmethod
    def _poke(db, table, display):
        obj = table.query.first()
        if display is False:
            return
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
        print(f'[{now}] [{"POKE":8}] [ * DB: {db.upper():15} | {table.__name__}]')

    @classmethod
    def awake(cls, config, modules, display):
        """Proceed every db which is available and random query a table to keep connection.
        :params config: flask config
        :type config: <class 'config.Config'>

        :params modules: db models pathname, it supposed to split by '.'
        :type modules: list['modelspath_1.models', 'modelspath_2.models']

        :return: keep db connection
        """
        db_binds = cls._get_db_binds(config)
        models_list = cls._get_models_list(modules)
        for db, table in cls._get_random_tables(db_binds, models_list).items():
            cls._poke(db=db, table=table, display=display)

    @staticmethod
    def _get_path():
        path_list = os.path.splitext(__file__)[0].strip('/').split('/')[1:]
        path = '.'.join(_ for _ in path_list)
        return path

    @staticmethod
    def _launch_scheduler(app, scheduler, task):
        """
        若 scheduler 不為空
            - 暫停scheduler
            - 插入任務
            - 重啟scheduler
        否則
            - 建立實體
            - 重啟app
            - 啟動scheduler
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
    def run(cls, app, config, modules, interval, display=False, scheduler=None):
        """Check scheduler, append task
        :params app: flask app
        :type app: <class 'flask.app.Flask'>

        :params config: flask config
        :type config: <class 'config.Config'>

        :params modules: db models pathname, it supposed to split by '.'
        :type modules: list, ['models_path_1.models', 'models_path_2.models']

        :params interval: awake task interval, unit=seconds
        :type interval: int

        :params display: to display activities of every poke
        :type display: bool

        :params scheduler: flask_apscheduler
        :type scheduler: <class 'flask_apscheduler.scheduler.APScheduler'>
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
        start = (datetime.now() + timedelta(seconds=interval)).strftime('%Y-%m-%d %H:%M:%S')
        display_mode = 'on' if display else 'off'
        print(f'[{now}] [{"INFO":8}] [ * Database Pacemaker is active 👻!]')
        print(f'[{now}] [{"INFO":8}] [ * Display mode: {display_mode}]')
        print(f'[{now}] [{"INFO":8}] [ * First round start at {start}]')

        task = {
            'id': 'keep_db_connection',
            'func': f'{cls._get_path()}:DatabasePacemaker.awake',
            'kwargs': {'config': config, 'modules': modules, 'display': display},
            'trigger': 'interval',
            'seconds': interval
        }

        cls._launch_scheduler(app=app, scheduler=scheduler, task=task)
