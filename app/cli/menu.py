import math
from dataclasses import dataclass
from typing import Callable

from .utils import print_color


class Menu:
    MENU_WIDTH = 100
    IDX_EXIT = "0"
    IDX_NEXT = "n"
    IDX_PREVIOUS = "p"

    @dataclass
    class MenuItem:
        idx: str = ""
        prompt: str = ""
        menu: Menu | Callable = None

    def __init__(self, title:str ="" , parent: Menu = None, max_rows: int=7, get_filter: Callable = None):
        self.upper_items: list[Menu.MenuItem] = []
        self.bottom_items: list[Menu.MenuItem] = []
        self.title = title
        self.get_filter = get_filter
        self.parent = parent
        self.max_rows = max_rows
        self.start_number = 0

        if self.parent:
            self.bottom_items.append(Menu.MenuItem("0", "Back", self.parent))
        else:
            self.bottom_items.append(Menu.MenuItem("0", "Exit", lambda x: exit(0)))

    def _print_header(self):
        print_color(f"{self.title:^{self.MENU_WIDTH}}", "black", "white")
        if self.get_filter:
            print_color(f"{self.get_filter():^{self.MENU_WIDTH}}", "black", "white")

    def _print_items(self):
        if not self.upper_items:
            print_color(f"│{'No results':^{self.MENU_WIDTH - 2}}│", "red")
            return

        rows_count = min(self.max_rows, max(1, len(self.upper_items)))
        cols_count = max(1, math.ceil(len(self.upper_items) / rows_count))
        matrix = [["" for _ in range(cols_count)] for _ in range(rows_count)]
        for idx, item in enumerate(self.upper_items):
            row, col = idx % rows_count, idx // rows_count
            matrix[row][col] = f"{idx + 1 + self.start_number :>2}. {item.prompt}"

        for item_formatter in (("│" + f"{{:{self.MENU_WIDTH // len(row) + self.MENU_WIDTH % len(row) - 2}}}"
                                * len(row) + "  " * (self.MENU_WIDTH % len(row))
                                + "│").format(*row) for row in matrix):
            print(item_formatter)

    def add_submenu(self, title: str, callback: Callable = None, get_filter: Callable = None) -> Menu:
        submenu = Menu(title=title, parent=self, get_filter=get_filter)
        self.add_upper_item(str(len(self.upper_items)), title, callback or submenu)
        return submenu

    def add_upper_item(self, idx: str, prompt: str, submenu: Menu | Callable):
        item = Menu.MenuItem(idx, prompt, submenu)
        self.upper_items.append(item)

    def add_bottom_item(self, idx: str, prompt: str, submenu: Menu | Callable):
        if not next(filter(lambda x : x.idx == idx, self.bottom_items), None):
            item = Menu.MenuItem(idx, prompt, submenu)
            self.bottom_items.insert(0, item)

    def remove_bottom_item(self, idx: str):
        if item := next(filter(lambda x : x.idx == idx, self.bottom_items), None):
            del item


    def _pring_bottom_items(self):
        #print("└" + "─" * (self.MENU_WIDTH - 2) + "┘")
        item_width = self.MENU_WIDTH // len(self.bottom_items)
        footer_text = []
        for item in self.bottom_items:
            footer_text.append(f"  {item.idx}. {item.prompt}".center(item_width))

        text = "".join(footer_text)
        print_color(text + " " * (self.MENU_WIDTH - len(text)), "black", bg="white")



    def _main_loop(self) -> Menu.MenuItem | None:
        self._print_header()
        self._print_items()
        self._pring_bottom_items()
        while index := input("Choice item: "):
            if index.isdigit() and 1 <= int(index) <= len(self.upper_items):
                return self.upper_items[int(index) - 1]

            if item := next((item for item in self.bottom_items if item.idx == index), None):
                return item

            print_color(f" {index} - Wrong choice ", bg="red")
        return None

    def run(self):
        item = self._main_loop()
        if item:
            if isinstance(item.menu, Callable):
                item.menu(item)
            else:
                item.menu.run()
