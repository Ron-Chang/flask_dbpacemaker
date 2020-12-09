import os, sys, inspect, importlib, random, sqlalchemy
from datetime import datetime, timedelta
from flask_apscheduler import APScheduler


class DBPacemaker:
    """
    Purpose:
        Keep multi-database awake during a long term crawler assignment.
        保持（複數）資料庫連線，當爬蟲進行長時間睡眠時。
    """
    @staticmethod
    def _get_now(format_=None):
        now = datetime.now()
        return now.strftime(format_) if format_ else now.strftime('%F %X,%f')[:-3]

    @staticmethod
    def _get_models_list(config):
        modules = getattr(config, 'MODELS_PATH_LIST')
        models = list()
        if isinstance(modules, str):
            importlib.import_module(modules)
            models.append(sys.modules[modules])
            return models
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
    def _get_all_tables(cls, db_binds, models_list):
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
        all_tables = cls._get_all_tables(db_binds, models_list)
        if not all_tables:
            return None
        return {db_name: cls._random_pick(tables) for db_name, tables in all_tables.items()}

    @classmethod
    def _poke(cls, db, table, db_name, display):
        try:
            table.query.first()
            if display:
                print(f'[{cls._get_now()}] [{"POKE":8}] [ * Flask-DBPacemaker 👻 {db_name.upper()} {table.__name__}]')
        except sqlalchemy.exc.ProgrammingError:
            print(f'[{cls._get_now()}] [{"WARNING":8}] [ * Flask-DBPacemaker 🐛 Cannot find {db_name.upper()} {table.__name__}]')
            db.session.rollback()
        except Exception as e:
            error = str(e).replace('\n', ' ')
            print(f'[{cls._get_now()}] [{"WARNING":8}] [ * Flask-DBPacemaker 🚨 {error}]')
            db.session.rollback()
        db.session.close()

    @classmethod
    def awake(cls, db, config, display):
        """
        Proceed every db which is available and random query a table to keep connection.
        對每個資料庫，做一次亂數取表單，透過請求表單第一個物件，保持db連線狀態。

        :param config: flask config
        :type config: <class 'config.Config'>
        """
        db_binds = cls._get_db_binds(config)
        models_list = cls._get_models_list(config)
        if not models_list:
            raise ImportError('ORM import failed, specify your orm in config.py e.g. MODELS_PATH_LIST = ["path.name"]')
        random_tables = cls._get_random_tables(db_binds, models_list)
        if not random_tables:
            raise ImportError('ORM import failed, specify your orm in config.py e.g. MODELS_PATH_LIST = ["path.name"]')
        for db_name, table in random_tables.items():
            cls._poke(db=db, table=table, db_name=db_name, display=display)

    @classmethod
    def _validate(cls, db, config):
        models_path_list = getattr(config, 'MODELS_PATH_LIST', None)
        if not models_path_list:
            raise ImportError('ORM import failed, specify your orm in config.py e.g. MODELS_PATH_LIST = ["path.name"]')
        cls.awake(db, config, display=False)

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
    def run(cls, app, db, config, display=True, scheduler=None):
        """
        Check scheduler for launching and appending awake task.
        檢查載入scheduler，插入喚醒db任務。

        :param app: flask app
        :type app: flask.app.Flask

        :param config: flask config
        :type config: <class 'config.Config'>

        :param display: to display activities of every poke
        :type display: bool

        :param scheduler: flask_apscheduler
        :type scheduler: flask_apscheduler.scheduler.APScheduler
        """
        cls._validate(db=db, config=config)

        switch = getattr(config, 'DB_PACEMAKER_SWITCH', True)
        interval = getattr(config, 'POKE_DB_INTERVAL', 60 * 60)

        status = 'inactive 🚫!'
        if switch:
            status = 'active 💓!'
            display_mode = 'active! ✅' if display else 'inactive! ❌'
            print(f'[{cls._get_now()}] [{"WARNING":8}] [ * Flask-DBPacemaker Debugger is {display_mode}]')
            cls._launch_scheduler(
                app=app,
                scheduler=scheduler,
                task={
                    'id': 'keep_db_connection',
                    'func': f'{cls._get_path()}:DBPacemaker.awake',
                    'kwargs': {'db': db, 'config': config, 'display': display},
                    'trigger': 'interval',
                    'seconds': interval
                }
            )
        print(f'[{cls._get_now()}] [{"INFO":8}] [ * Flask-DBPacemaker is {status}]')

