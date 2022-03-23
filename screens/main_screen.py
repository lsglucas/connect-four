import sys

import math
import pygame as pg

from multiplayer import Server, Client
from screens.ending_screens import EndingScreen
from screens.menu import OptionsMenu
from utils import Controller, Settings
from utils.utilities import UtilitiesMain

"""
The second most important file, it creates the game itself (board, esc menu, check who is the winner and so on),
and calls important classes and functions like the esc menu which pauses the game when pressed esc,
as well as most utilities functions
"""


class MainScreen:
    def __init__(
            self,
            screen,
            is_controller,
            option: str,
            server: Server,
            client: Client,
    ) -> None:
        self.config = Settings()
        self.option = option
        self.server = server
        self.client = client

        self.screen: pg.Surface = screen
        self.background_image: pg.Surface = self.config.bg_image
        self.is_controller: bool = is_controller

        self.sound_chip_1 = self.config.sound_chip_1
        self.sound_chip_2 = self.config.sound_chip_2
        self.volume = self.config.volume
        self.chip_1 = self.config.chip_1
        self.chip_2 = self.config.chip_2
        self.ai_chip: int = 2

    def main_screen(self, scores: list, usernames: list):
        """Main function to call the game screen"""

        control = Controller()
        utilities = UtilitiesMain(self.screen, self.server, self.client)

        start_time = pg.time.get_ticks()  # Used for timer

        attr = {
            "res": self.config.size,
            "style": self.config.style,
            "label": self.config.op_label,
            "resume": self.config.op_resume,
            "st_menu": self.config.op_start_menu,
            "quit": self.config.op_quit,
            "theme": self.config.theme,
        }
        menu = OptionsMenu(**attr)  # Initializes the Options Menu class which is used to create the esc menu

        clock = pg.time.Clock()

        matrix = utilities.create_matrix()

        chip = self.chip_2 if self.option == "Player vs Player" else self.chip_1

        close_loop: bool = False

        x, y = 950, 15

        player_turn: int = 1  # if not option else option

        self.client.add_player_move(utilities.playersTurn)
        self.client._last_move_data = {str(value): value for value in [
            0,
            matrix,
            player_turn,
            self.sound_chip_1,
            self.sound_chip_2,
            usernames,
            start_time,
            scores,
            self.option,
        ]}

        pg.mixer.music.play(loops=-1)
        pg.mixer.music.set_volume(self.volume)

        while not close_loop:
            pg.mouse.set_visible(False)
            utilities.draw_board(matrix, start_time, usernames)

            self.screen.blit(chip, (x, y))

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    close_loop = True
                    sys.exit()

                if self.is_controller:
                    if control.checkController():
                        x = control.x_hd
                        y = 8

                if event.type == pg.MOUSEMOTION:
                    x = event.pos[0]
                    y = event.pos[1]

                if event.type == pg.MOUSEBUTTONDOWN:
                    save_chip = chip

                    print(player_turn)

                    column = utilities.location_X(pg.mouse.get_pos()[0])

                    if column != 0:
                        response = self.client.move_chip(
                            column,
                            matrix,
                            player_turn,
                            self.sound_chip_1,
                            self.sound_chip_2,
                            usernames,
                            start_time,
                            scores,
                            self.option,
                        )

                        (play_again, player_turn, chip, scores) = response[:4]

                        if play_again is not None:
                            return play_again

                        if chip is None:
                            chip = save_chip

                if self.is_controller:
                    if control.is_controller_drop_event(event):
                        save_chip = chip

                        column = utilities.location_X(control.get_x_pos(event))
                        if column != 0:
                            response = self.client.move_chip(
                                column,
                                matrix,
                                player_turn,
                                self.sound_chip_1,
                                self.sound_chip_2,
                                usernames,
                                start_time,
                                scores,
                                self.option,
                            )

                            (play_again, player_turn, chip, scores) = response[:4]

                            if play_again is not None:
                                return play_again

                            if chip is None:
                                chip = save_chip

                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        play_again = menu.run(self.screen, clock)
                        if not play_again:
                            return play_again

                if control.is_controller_esc_event(event):
                    play_again = menu.run(self.screen, clock)
                    if not play_again:
                        return play_again

                if control.is_controller_esc_event(event):
                    screen = self.screen
                    control.check_event(event)

            if self.option == "Player vs AI" and player_turn % 2 == 1:
                column, minimax_score = utilities.minimaxTree(
                    matrix, 5, -math.inf, math.inf, True
                )

                pg.time.wait(200)

                if utilities.is_available(matrix, column):
                    row = utilities.get_open_row(matrix, column)
                    utilities.drop_piece(matrix, row, column, self.ai_chip)
                    self.sound_chip_1.play()

                    if utilities.is_victory(matrix, self.ai_chip):
                        scores[1] += 1

                        utilities.draw_board(matrix, start_time, usernames)

                        pg.display.update()

                        pg.time.wait(1500)

                        data = {usernames[0]: scores[0], usernames[1]: scores[1]}

                        ending = EndingScreen(
                            self.screen,
                            data,
                            res=self.config.size,
                            pg_res=self.config.win_pg,
                            sm_res=self.config.win_sm,
                            quit_res=self.config.win_quit,
                            lb_res=self.config.win_ld,
                        )

                        play_again = ending.scores()

                        return play_again

                    player_turn += 1
                    player_turn = player_turn % 2

            pg.display.update()

            clock.tick(75)
