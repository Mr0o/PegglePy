import time

import pygame

from editor import levelEditor
from loadLevelMenu import loadLevelMenu
from local.game import Game
from local.peg import createPegColors
from menu import getPauseScreen, mainMenu
from settingsMenu import settingsMenu


class MenuController:
    def start(
        self, screen: pygame.Surface, clock: pygame.time.Clock, game: Game
    ) -> tuple[str, str]:
        selection = "none"
        editor_selection = "none"
        while selection not in ("start", "quit"):
            selection = mainMenu(screen)
            if selection == "quit":
                game.gameRunning = False
            elif selection == "editor":
                time.sleep(0.5)
                editor_selection, game.pegs = levelEditor(screen, clock)
                if editor_selection == "quit":
                    game.gameRunning = False
                    selection = "quit"
                elif editor_selection == "play":
                    game.originPegs = game.pegs.copy()
                    self._prepare_editor_level(game, game.pegs)
                    selection = "start"
            elif selection == "settings":
                time.sleep(0.15)
                if settingsMenu(screen) == "mainMenu":
                    selection = "none"
        return selection, editor_selection

    def pause_selection(
        self, screen: pygame.Surface, mouse_x: int, mouse_y: int, clicked: bool
    ) -> str:
        pause_screen, selection = getPauseScreen(mouse_x, mouse_y, clicked)
        screen.blit(pause_screen, (0, 0))
        return selection

    def navigate_main_menu(
        self, screen: pygame.Surface, clock: pygame.time.Clock, game: Game
    ) -> tuple[str, bool]:
        selection = "mainMenu"
        editor_played = False
        while selection == "mainMenu":
            selection = mainMenu(screen)
            if selection == "quit":
                game.gameRunning = False
            elif selection == "editor":
                time.sleep(0.5)
                editor_selection, editor_pegs = levelEditor(screen, clock)
                if editor_selection == "quit":
                    game.gameRunning = False
                elif editor_selection == "mainMenu":
                    selection = "mainMenu"
                elif editor_selection == "play":
                    game.originPegs = editor_pegs.copy()
                    self._prepare_editor_level(game, editor_pegs)
                    editor_played = True
                    selection = "start"
            elif selection == "settings":
                if settingsMenu(screen) == "mainMenu":
                    selection = "mainMenu"
        return selection, editor_played

    def open_editor(
        self,
        screen: pygame.Surface,
        clock: pygame.time.Clock,
        game: Game,
    ) -> tuple[str, bool]:
        time.sleep(0.5)
        editor_selection, editor_pegs = levelEditor(
            screen, clock, False, game.originPegs.copy()
        )
        if editor_selection == "play":
            game.originPegs = editor_pegs.copy()
            self._prepare_editor_level(game, editor_pegs)
            return editor_selection, True
        if editor_selection == "mainMenu":
            _, editor_played = self.navigate_main_menu(screen, clock, game)
            return editor_selection, editor_played
        if editor_selection == "quit":
            game.gameRunning = False
        return editor_selection, False

    def open_settings(self, screen: pygame.Surface) -> None:
        settingsMenu(screen)
        pygame.event.clear(pygame.MOUSEBUTTONDOWN)
        while pygame.mouse.get_pressed()[0]:
            pygame.event.pump()

    def select_level(
        self, screen: pygame.Surface
    ) -> tuple[list, list, int, str]:
        return loadLevelMenu(screen)

    def load_selected_level(self, screen: pygame.Surface, game: Game) -> str:
        pegs, origin_pegs, orange_count, level_name = self.select_level(screen)
        game.pegs = pegs
        game.originPegs = origin_pegs
        game.orangeCount = orange_count
        return level_name

    @staticmethod
    def _prepare_editor_level(game: Game, pegs: list) -> None:
        game.pegs = createPegColors(pegs.copy())
        game.orangeCount = sum(peg.color == "orange" for peg in game.pegs)
