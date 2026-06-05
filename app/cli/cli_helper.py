import textwrap

from app.cli.menu import Menu
from app.cli.utils import color_text, truncate_visible, visible_length
from app.db.model import Category, Film, Period, UserQuery
from app.db.repository import SakilaRepo


class CLIHelper:
    """Coordinate menu callbacks and repository calls for the CLI application."""

    POPULAR_QUERY_COLUMNS_COUNT = 4
    POPULAR_QUERY_INDEX_WIDTH = 4
    POPULAR_QUERY_SEPARATOR = " | "

    # ************* Listeners *****************
    def on_category_change_listener(self, item: Menu.MenuItem) -> None:
        """Apply the selected category filter and reset pagination."""
        self.user_query.category = Category(int(item.idx), item.prompt)
        self.repo.current_page = 0

    def on_period_change_listener(self, item: Menu.MenuItem) -> None:
        """Apply the selected release-year period and reset pagination."""
        self.user_query.years = Period(int(item.idx), item.prompt)
        self.repo.current_page = 0

    def on_title_change_listener(self, _) -> None:
        """Read a title filter from input and reset pagination."""
        self.user_query.title = input("Enter title for search: ") or None
        self.repo.current_page = 0

    def on_popular_query_listener(self, _=None) -> None:
        """Show saved popular filters and apply the selected one."""
        popular_queries = self.repo.get_popular_queries(5)
        popular_menu = Menu(
            "Popular filters", self.main_menu, get_filter=self._get_fiter
        )
        popular_menu.max_rows = 5

        def select_popular_filter(item: Menu.MenuItem) -> None:
            """Apply a selected popular query."""
            self.user_query = popular_queries[int(item.idx)]
            self.repo.current_page = 0

        for idx, query in enumerate(popular_queries):
            popular_menu.add_upper_item(
                str(idx), self._get_popular_query_label(query), select_popular_filter
            )

        popular_menu.run()

    def on_film_search_listener(self, _=None, save_history: bool = True) -> None:
        """Run film search with the current filters and render paginated results."""

        def next_page(_) -> None:
            """Move to the next page of search results."""
            self.repo.current_page += 1
            self.on_film_search_listener(save_history=False)

        def previous_page(_) -> None:
            """Move to the previous page of search results."""
            self.repo.current_page -= 1
            self.on_film_search_listener(save_history=False)

        def show_film_info(item: Menu.MenuItem) -> None:
            """Show detailed information for the selected film."""
            film = films_by_id.get(int(item.idx))
            if film is None:
                return

            film_info_menu = Menu(film.title, film_menu)
            film_info_menu.max_rows = 99999
            for line in self._get_film_info_lines(film):
                film_info_menu.add_info_item(line)
            film_info_menu.run()

        if save_history:
            self.repo.current_page = 0
            self.repo.save_query(self.user_query)

        category_id = self._get_selected_category_id()
        period = self._get_selected_period()
        search_title = self.user_query.title
        film_menu = Menu(self._get_fiter(), self.main_menu)
        film_menu.max_rows = 99999
        film_menu.start_number = self.repo.current_page * self.repo.FILMS_ON_PAGE
        pattern = f"{{:{40}}} {{:^{5}}} {{:{15}}} {{:{5}}}"
        films_on_page = list(self.repo.get_films(category_id, period, search_title))
        films_by_id = {film.film_id: film for film in films_on_page}
        for film in films_on_page:
            display_title = self._get_display_title(film)
            film_menu.add_upper_item(
                str(film.film_id),
                pattern.format(
                    display_title, film.release_year, film.category, film.rating
                ),
                show_film_info,
            )

        if self.repo.current_page > 0:
            film_menu.add_bottom_item(Menu.IDX_PREVIOUS, "Previous", previous_page)
        if len(films_on_page) == self.repo.FILMS_ON_PAGE:
            film_menu.add_bottom_item(Menu.IDX_NEXT, "Next", next_page)

        film_menu.run()

    # ************* Listeners *****************

    def __init__(self, repo: SakilaRepo):
        """Create a CLI helper bound to a film repository."""
        self.repo: SakilaRepo = repo
        self.user_query: UserQuery = UserQuery()
        self.main_menu = Menu("Main menu", get_filter=self._get_fiter)

    def _get_fiter(self) -> str:
        """Return a formatted label with currently active filters."""
        category_name = (
            self.user_query.category.name if self.user_query.category else "All"
        )
        period_name = self.user_query.years.period if self.user_query.years else "All"
        cat = f" Category: {category_name} "
        period = f" Period: {period_name} "
        title = f" Title: {self.user_query.title or 'All'} "
        padding = Menu.MENU_WIDTH - len(cat) - len(period) - len(title)
        left_padding = padding // 2
        right_padding = padding - left_padding
        return "".join(
            [
                color_text(" " * left_padding, fg="black", bg="white"),
                color_text(cat, bg="blue"),
                color_text(period, bg="green"),
                color_text(title, bg="magenta"),
                color_text(" " * right_padding, fg="black", bg="white"),
            ]
        )

    def _get_popular_query_label(self, query: UserQuery) -> str:
        """Return a menu label for a popular query."""
        columns = [
            f"Category: {query.category.name if query.category else 'All'}",
            f"Period: {query.years.period if query.years else 'All'}",
            f"Title: {query.title or 'All'}",
            f"Count: {query.count or 0}",
        ]
        width = self._get_popular_query_column_width()
        return self.POPULAR_QUERY_SEPARATOR.join(
            self._format_popular_query_column(column, width) for column in columns
        )

    def _get_popular_query_column_width(self) -> int:
        """Return equal width for popular-query columns."""
        available_width = (
            Menu.MENU_WIDTH
            - 2
            - self.POPULAR_QUERY_INDEX_WIDTH
            - len(self.POPULAR_QUERY_SEPARATOR) * (self.POPULAR_QUERY_COLUMNS_COUNT - 1)
        )
        return available_width // self.POPULAR_QUERY_COLUMNS_COUNT

    def _format_popular_query_column(self, text: str, width: int) -> str:
        """Trim and pad a popular-query column to fixed visible width."""
        text = truncate_visible(text, width)
        return text + " " * (width - visible_length(text))

    def _get_selected_category_id(self) -> int | None:
        """Return selected category id or None when all categories are selected."""
        if not self.user_query.category:
            return None
        if self.user_query.category.category_id == Category.ALL:
            return None
        return self.user_query.category.category_id

    def _get_selected_period(self) -> str | None:
        """Return selected period label or None when all periods are selected."""
        if not self.user_query.years:
            return None
        if not self.user_query.years.id:
            return None
        return self.user_query.years.period

    def _get_display_title(self, film: Film) -> str:
        """Return film title with highlighted search term when title filter is set."""
        if not self.user_query.title:
            return film.title

        search_title = self.user_query.title.upper()
        return film.title.replace(search_title, color_text(search_title, fg="blue"))

    def _get_film_info_lines(self, film: Film) -> list[str]:
        """Return formatted film details for the film information menu."""
        description = film.description or "No description"
        wrapped_description = textwrap.wrap(
            description, width=Menu.MENU_WIDTH - 18
        ) or [description]
        lines = [
            f"Film ID: {film.film_id}",
            f"Title: {film.title}",
            f"Category: {film.category}",
            f"Release year: {film.release_year}",
            f"Rating: {film.rating}",
            f"Length: {film.length} min",
            f"Language ID: {film.language_id}",
            f"Special features: {film.special_features or 'No special features'}",
            "Description:",
        ]
        lines.extend(f"  {line}" for line in wrapped_description)
        return lines

    def start_main_thread(self) -> None:
        """Build and run the main interactive menu loop."""
        category_menu = self.main_menu.add_submenu(
            "Set filter by category", get_filter=self._get_fiter
        )
        period_menu = self.main_menu.add_submenu(
            "Set filter by period", get_filter=self._get_fiter
        )
        self.main_menu.add_submenu("Set filter by title", self.on_title_change_listener)
        self.main_menu.add_submenu("Last popular query", self.on_popular_query_listener)
        self.main_menu.add_submenu("Search films", self.on_film_search_listener)

        for period_item in self.repo.get_year():
            period_menu.add_upper_item(
                str(period_item.id), period_item.period, self.on_period_change_listener
            )

        for category_item in self.repo.get_category():
            category_menu.add_upper_item(
                str(category_item.category_id),
                category_item.name,
                self.on_category_change_listener,
            )

        while True:
            self.main_menu.run()
