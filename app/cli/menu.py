from __future__ import annotations

import math
import sys
from collections.abc import Callable
from dataclasses import dataclass

from .utils import clear_console, print_color, truncate_visible, visible_length


class Menu:
    """Interactive terminal menu with upper content items and bottom actions."""

    MENU_WIDTH = 80
    IDX_EXIT = "0"
    IDX_NEXT = "n"
    IDX_PREVIOUS = "p"

    @dataclass
    class MenuItem:
        """Single menu item definition."""

        idx: str = ""
        prompt: str = ""
        menu: Menu | Callable | None = None

    def __init__(
        self,
        title: str = "",
        parent: Menu | None = None,
        max_rows: int = 7,
        get_filter: Callable | None = None,
    ):
        """Create a menu with optional parent navigation and filter label."""
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
            self.bottom_items.append(Menu.MenuItem("0", "Exit", lambda _: sys.exit(0)))

    def _print_header(self) -> None:
        """Print the menu title and active filter label."""
        print_color(f"{self.title:^{self.MENU_WIDTH}}", "black", "white")
        if self.get_filter:
            print_color(f"{self.get_filter():^{self.MENU_WIDTH}}", "black", "white")

    def _print_items(self) -> None:
        """Print upper menu items in a compact column layout."""
        if not self.upper_items:
            print_color(f"│{'No results':^{self.MENU_WIDTH - 2}}│", "red")
            return

        rows_count = min(self.max_rows, max(1, len(self.upper_items)))
        cols_count = max(1, math.ceil(len(self.upper_items) / rows_count))
        matrix = [["" for _ in range(cols_count)] for _ in range(rows_count)]
        for idx, item in enumerate(self.upper_items):
            row, col = idx % rows_count, idx // rows_count
            matrix[row][col] = (
                f"{idx + 1 + self.start_number:>2}. {item.prompt}"
                if item.idx
                else f"    {item.prompt}"
            )

        for row in matrix:
            inner_width = self.MENU_WIDTH - 2
            base_width = inner_width // len(row)
            extra_width = inner_width % len(row)
            widths = [
                base_width + (1 if idx < extra_width else 0)
                for idx in range(len(row))
            ]
            cells = []
            for item, width in zip(row, widths):
                item = truncate_visible(item, width)
                cells.append(item + " " * (width - visible_length(item)))
            print("│" + "".join(cells) + "│")

    def add_submenu(
        self,
        title: str,
        callback: Callable | None = None,
        get_filter: Callable | None = None,
    ) -> Menu:
        """Create a child menu and register it as an upper item."""
        submenu = Menu(title=title, parent=self, get_filter=get_filter)
        self.add_upper_item(str(len(self.upper_items)), title, callback or submenu)
        return submenu

    def add_upper_item(self, idx: str, prompt: str, submenu: Menu | Callable) -> None:
        """Add a selectable item to the main menu area."""
        item = Menu.MenuItem(idx, prompt, submenu)
        self.upper_items.append(item)

    def add_info_item(self, prompt: str) -> None:
        """Add a non-action item to the main menu area."""
        item = Menu.MenuItem("", prompt, None)
        self.upper_items.append(item)

    def add_bottom_item(self, idx: str, prompt: str, submenu: Menu | Callable) -> None:
        """Add a bottom action when an action with the same index is absent."""
        if not next(filter(lambda item: item.idx == idx, self.bottom_items), None):
            item = Menu.MenuItem(idx, prompt, submenu)
            self.bottom_items.insert(0, item)

    def remove_bottom_item(self, idx: str) -> None:
        """Remove a bottom action by its index."""
        self.bottom_items = [item for item in self.bottom_items if item.idx != idx]

    def _print_bottom_items(self) -> None:
        """Print bottom navigation actions."""
        item_width = self.MENU_WIDTH // len(self.bottom_items)
        footer_text = []
        for item in self.bottom_items:
            footer_text.append(f"  {item.idx}. {item.prompt}".center(item_width))

        text = "".join(footer_text)
        print_color(text + " " * (self.MENU_WIDTH - len(text)), "black", bg="white")

    def _main_loop(self) -> Menu.MenuItem | None:
        """Read user input until a valid menu item is selected."""
        self._print_header()
        self._print_items()
        self._print_bottom_items()
        while index := input("Choice item: "):
            if index.isdigit() and 1 <= int(index) <= len(self.upper_items):
                return self.upper_items[int(index) - 1]

            if item := next(
                (item for item in self.bottom_items if item.idx == index), None
            ):
                return item

            print_color(f" {index} - Wrong choice ", bg="red")
        return None

    def run(self) -> None:
        """Run the menu and dispatch the selected item."""
        item = self._main_loop()
        if item:
            clear_console()
            if isinstance(item.menu, Callable):
                item.menu(item)
            elif isinstance(item.menu, Menu):
                item.menu.run()
            else:
                self.run()
