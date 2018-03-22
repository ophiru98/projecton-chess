import os
import errno
import hardware as hw
import chess_helper_2 as ch
import find_moves_rank as fm
import photos_angle_2
import chess_engine_wrapper
import gui_img_manager
import cv2
import numpy as np
import tester_helper
import filter_colors_2
"""
Main logic file.
"""
SOURCE = True
LEFT = 0
RIGHT = 1
ROWS_NUM = 8
RESULTS_DIR = 'super_tester_results'


class game_loop_2:
    def __init__(self, angles_num, user_moves_if_test=None,rival_moves_if_test=None, imgs_if_test=None, if_save_and_print=True, net_dir_name = None):
        self.if_save_and_print = if_save_and_print
        if if_save_and_print:
            tester_helper.make_squares_dirs()

        self.moves_counter = 0
        self.last_move = None

        if user_moves_if_test is not None:
            self.is_test = True
            self.net_dir_name = net_dir_name
            self.user_moves = user_moves_if_test
            self.rival_moves = rival_moves_if_test
        else:
            self.is_test = False

        self.hardware = hw.hardware(angles_num, imgs_if_test)
        self.chesshelper = ch.chess_helper_2(ch.chess_helper_2.USER)
        self.delay_chesshelper = ch.chess_helper_2(ch.chess_helper_2.USER)
        self.ph_angles = []
        if not self.is_test:
            gui_img_manager.set_finished(False)

        for i in range(angles_num):
            if not self.is_test:
                gui_img_manager.set_camera(i)
            self.ph_angles.append(photos_angle_2.photos_angle_2(self.hardware, self.chesshelper, self.delay_chesshelper, i))
            self.ph_angles[i].prep_img()

        for ang in self.ph_angles:
            ang.init_colors()

        if not self.is_test:
            gui_img_manager.set_finished(True)

        self.movefinder = fm.find_moves_rank(self.chesshelper, self.net_dir_name)
        self.chess_engine = chess_engine_wrapper.chess_engine_wrapper()


    def main(self):
        while True:
            if self.is_test and self.moves_counter >= len(self.user_moves):
                print('Done')
                break
            gui_img_manager.set_finished(False)
            self.play_user_turn()
            if self.if_save_and_print:
                print(self.chesshelper.board)
            last_move = self.get_rival_move()
            if self.if_save_and_print:
                print(self.chesshelper.board)
            gui_img_manager.set_finished(True)

    def play_user_turn(self):
        self.best_move = self.chess_engine.get_best_move(self.last_move)
        if self.if_save_and_print:
            print("I recommend: " + self.best_move)
        if not self.is_test:
            self.hardware.player_indication(self.best_move)
        else:
            self.best_move = self.user_moves[self.moves_counter]
            print("sorry, I changed my mind. play" + str(self.best_move))

        self.chesshelper.do_turn(self.best_move[0], self.best_move[1])

    def get_rival_move(self):
        if self.if_save_and_print:
            print("\n" + "move num" + str(self.moves_counter))

        # real move: only if test
        rival_move = None
        if (self.is_test):
            rival_move = self.rival_moves[self.moves_counter]

        # get relevant squares
        relevant_squares = self.chesshelper.get_relevant_locations()
        sources = relevant_squares[0]
        dests = relevant_squares[1]
        pairs = []
        pairs_ranks = []

        #get two images per iteration, untill has one abs good move
        cnt = 0
        to_continue = True
        while to_continue and (len(pairs) == 0 or len(pairs_ranks) == 0):
            try:
                if self.is_test:
                    to_continue = False
                for i in range(len(self.ph_angles)):
                    if cnt > 0:
                        print("id error plz take another photo k thnx")
                    gui_img_manager.set_camera(i)
                    self.ph_angles[i].prep_img()
                    pairs_and_ranks = self.check_one_direction(sources, dests, angle_idx=i)
                    gui_img_manager.reset_images(i)
                    pairs = pairs + pairs_and_ranks[0]
                    pairs_ranks = pairs_ranks + pairs_and_ranks[1]
                cnt += 1
                best_pair_idx = [i for i in range(len(pairs_ranks)) if pairs_ranks[i] == max(pairs_ranks)][0]
                move = pairs[best_pair_idx]
            except:
                move = ' both direction failed'

        if self.if_save_and_print:
            print("detected_move")
            print(move)
            print('rival_move')
            print(rival_move)

        if self.is_test:
            move = rival_move
        self.last_move = move
        self.chesshelper.do_turn(move[0], move[1])

        # delayed helper do his turn now for filter_colors needs
        self.delay_chesshelper.do_turn(self.best_move[0],self.best_move[1])
        self.delay_chesshelper.do_turn(move[0], move[1])
        self.moves_counter += 1
        return move

    def check_one_direction(self, sources, dests, angle_idx):
        try:

            if self.if_save_and_print:
                print("angle_num_" + str(angle_idx))
                tester_helper.make_dir(RESULTS_DIR + '\\' + 'by_move/move_num_' + str(self.moves_counter) + '/angle_num_' + str(angle_idx))

            rival_move = None
            if (self.is_test):
                rival_move = self.rival_moves[self.moves_counter]

            angle = self.ph_angles[angle_idx]
            cut_board_im = angle.get_new_img(tester_info=(self.moves_counter, angle_idx))
            sourcesims, sourcesabvims = self.get_diff_im_and_dif_abv_im_list(sources, cut_board_im, angle,
                                                                             SOURCE)
            destsims, destsabvims = self.get_diff_im_and_dif_abv_im_list(dests, cut_board_im, angle,
                                                                         not SOURCE)
            pairs, pairs_rank = self.movefinder.get_move(sources, sourcesims, sourcesabvims, dests, destsims, destsabvims,
                                                         tester_info = (rival_move, self.moves_counter,angle_idx))
            board_before = angle.get_board_test(True)
            angle.update_board()
            if self.if_save_and_print:
                above_src = [self.chesshelper.get_square_above(src) for src in sources]
                above_trgt = [self.chesshelper.get_square_above(trgt) for trgt in dests]
                source_big_im = tester_helper.make_board_im_helper(sources+above_src,sourcesims+sourcesabvims)
                tester_helper.save_bw(np.array(source_big_im), "board", self.moves_counter, angle_idx, "src_big_im")
                target_big_im = tester_helper.make_board_im_helper(dests+above_trgt,destsims+destsabvims)
                tester_helper.save_bw(np.array(target_big_im), "board", self.moves_counter, angle_idx, "trgt_big_im")
                before_big_im = tester_helper.make_board_im_helper(list(board_before.keys()),list(board_before.values()),True)
                tester_helper.save_colors(before_big_im,"board",self.moves_counter,angle_idx,"berko")

            ### save prev picture ###
            angle.set_prev_im(cut_board_im)

            return pairs, pairs_rank
        except:
            print("angle " + str(angle_idx) + " failed")
            return [], []

    def get_diff_im_and_dif_abv_im_list(self, locs, cut_board_im, angle, is_source):
        try:
            locsims = []
            locsabvims = []
            for loc in locs:
                abv_loc = self.chesshelper.get_square_above(loc)
                diff_im = angle.get_square_diff(cut_board_im, loc, is_source)
                diff_abv_im = angle.get_square_diff(cut_board_im, abv_loc, is_source)
                locsims.append(diff_im)
                locsabvims.append(diff_abv_im)
            return locsims, locsabvims

        except Exception as e:
            if is_source:
                b_val ="source"
            else:
                b_val="target"
            print("get_dif_im ("+b_val+")_failed" )
            print(str(e))
            raise
    




