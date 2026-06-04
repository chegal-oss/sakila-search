from app.cli.menu import Menu
from app.cli.utils import color_text
from app.db.model import UserQuery, Category, Period
from app.db.repository import SakilaRepo


class CLIHelper:

    # ************* Listeners *****************
    def on_category_change_listener(self, item: Menu.MenuItem):
        self.user_query.category = Category(int(item.idx), item.prompt)
        self.repo.current_page = 0

    def on_period_change_listener(self, item: Menu.MenuItem):
        self.user_query.years = Period(int(item.idx), item.prompt)
        self.repo.current_page = 0

    def on_title_change_listener(self, _):
        self.user_query.title = input("Enter title for search: ") or None
        self.repo.current_page = 0

    def on_popular_query_listener(self, _=None):
        popular_queries = self.repo.get_popular_queries(5)
        popular_menu = Menu("Popular filters", self.main_menu, get_filter=self._get_fiter)
        popular_menu.max_rows = 5

        def select_popular_filter(item: Menu.MenuItem):
            self.user_query = popular_queries[int(item.idx)]
            self.repo.current_page = 0

        for idx, query in enumerate(popular_queries):
            popular_menu.add_upper_item(str(idx), self._get_popular_query_label(query), select_popular_filter)

        popular_menu.run()

    def on_film_search_listener(self, _=None, save_history: bool = True):

        def next_page(_):
            self.repo.current_page += 1
            self.on_film_search_listener(save_history=False)

        def previous_page(_):
            self.repo.current_page -= 1
            self.on_film_search_listener(save_history=False)

        def show_film_info(item):
            pass

        if save_history:
            self.repo.current_page = 0
            self.repo.save_query(self.user_query)

        category_id = (
            self.user_query.category.category_id
            if self.user_query.category and self.user_query.category.category_id
            else None
        )
        period = self.user_query.years.period if self.user_query.years and self.user_query.years.id else None
        title = self.user_query.title
        film_menu = Menu(self._get_fiter(), self.main_menu)
        film_menu.max_rows = 99999
        film_menu.start_number = self.repo.current_page * self.repo.FILMS_ON_PAGE
        pattern = f"{{:{40}}} {{:^{5}}} {{:{15}}} {{:{5}}}"
        films_on_page = list(self.repo.get_films(category_id, period, title))
        for film in films_on_page:
            title = film.title if not self.user_query.title else film.title.replace(self.user_query.title.upper(),
                                                                                    color_text(
                                                                                        self.user_query.title.upper(),
                                                                                        fg="blue"))
            film_menu.add_upper_item(str(film.film_id),
                                     pattern.format(title, film.release_year, film.category, film.rating),
                                     show_film_info)

        if self.repo.current_page > 0:
            film_menu.add_bottom_item(Menu.IDX_PREVIOUS, "Previous", previous_page)
        if len(films_on_page) == self.repo.FILMS_ON_PAGE:
            film_menu.add_bottom_item(Menu.IDX_NEXT, "Next", next_page)

        film_menu.run()

    # ************* Listeners *****************

    def __init__(self, repo: SakilaRepo):
        self.repo: SakilaRepo = repo
        self.user_query: UserQuery = UserQuery()
        self.main_menu = Menu("Main menu", get_filter=self._get_fiter)

    def _get_fiter(self) -> str:
        cat = f" Category: {self.user_query.category.name if self.user_query.category else 'All'} "
        period = f" Period: {self.user_query.years.period if self.user_query.years else 'All'} "
        title = f" Title: {self.user_query.title or 'All'} "
        padding = Menu.MENU_WIDTH - len(cat) - len(period) - len(title)
        left_padding = padding // 2
        right_padding = padding - left_padding
        return "".join([
            color_text(" " * left_padding, fg="black", bg="white"),
            color_text(cat, bg="blue"),
            color_text(period, bg="green"),
            color_text(title, bg="magenta"),
            color_text(" " * right_padding, fg="black", bg="white"),
        ])

    def _get_popular_query_label(self, query: UserQuery) -> str:
        searched_at = ""
        if query.last_searched_at:
            searched_at = f" | Last: {query.last_searched_at.astimezone().strftime('%Y-%m-%d %H:%M')}"
        return f"{query.to_label()} | Count: {query.count or 0}{searched_at}"


    def start_main_thread(self):
        category_menu = self.main_menu.add_submenu("Set category", get_filter=self._get_fiter)
        period_menu = self.main_menu.add_submenu("Set period", get_filter=self._get_fiter)
        self.main_menu.add_submenu("Set filter by title", self.on_title_change_listener)
        self.main_menu.add_submenu("Select popular", self.on_popular_query_listener)
        self.main_menu.add_submenu("Search films", self.on_film_search_listener)

        for period_item in self.repo.get_year():
            period_menu.add_upper_item(str(period_item.id), period_item.period, self.on_period_change_listener)

        for category_item in self.repo.get_category():
            category_menu.add_upper_item(str(category_item.category_id), category_item.name,
                                         self.on_category_change_listener)

        while True:
            self.main_menu.run()
