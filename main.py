from app import db
from app.cli import utils
from app.cli.cli_helper import CLIHelper
from app.db.repository import SakilaRepo

if __name__ == "__main__":
    print(utils.sakila_banner())
    with (
        db.connect(db.FallbackConnector) as sql_connection,
        db.FallbackHistoryConnector() as history_connection,
    ):
        CLIHelper(SakilaRepo(sql_connection, history_connection)).start_main_thread()
