from app import db
from app.cli.cli_helper import CLIHelper
from app.db import MongoHistoryConnector
from app.db.repository import SakilaRepo



if __name__ == "__main__":
    with db.connect(db.MySQLConnector) as sql_connection, MongoHistoryConnector() as mongo_history:
        CLIHelper(SakilaRepo(sql_connection, mongo_history)).start_main_thread()

