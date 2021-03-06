import cv2
import filter_colors_2
import identify_board
import board_cut_fixer
import tester_helper
import numpy as np
import mygui
print_and_save = False


class photos_angle_2:
    def __init__(self, hardware1, chess_helper, delay_chess_helper, self_idx):
        self.chess_helper = chess_helper
        self.delay_chess_helper = delay_chess_helper
        self.hardware = hardware1
        self.idx = self_idx
        self.boardid = identify_board.identify_board()
        self.fixer = board_cut_fixer.board_cut_fixer()

    def init_colors(self):
        ## first time - must be a good photo!
        while True:
            try:
                self.prep_img()
                cut_board_im = self.get_new_img(tester_info=(-1, self.idx))
                break
            except Exception as e:
                print(e)
                print("init colors - please take another photo")
        self.color_filter = filter_colors_2.filter_colors_2(cut_board_im, self.chess_helper,
                                                                      self.delay_chess_helper)

    def prep_img(self):
        self.prep_im = self.hardware.get_image(self.idx, board_cut_fixer.FixerErrorType.NoDirection.value)

    def get_new_img(self, tester_info=None):
        try:
            to_save = bool(tester_info)
            new_board_im = self.prep_im
            mygui.add_angle_image(new_board_im)
            better_cut_board_im = self.fixer.main(new_board_im)
            mygui.add_angle_image(better_cut_board_im)
            # better_cut_board_im = new_board_im

            if to_save:
                move_num = tester_info[0]
                angle_idx = tester_info[1]
                tester_helper.save_bw(new_board_im,'board', move_num,
                                          angle_idx, 'first')
                tester_helper.save_bw(better_cut_board_im, 'board', move_num, angle_idx, 'second')

            return better_cut_board_im
        except:
            cv2.imshow("image", new_board_im)
            cv2.waitKey(1000)
            cv2.destroyAllWindows()
            print("get new im failed")
            raise Exception()

    def get_square_diff(self, cut_board_im, src, is_source):
        return self.color_filter.get_square_diff(cut_board_im, src, is_source)

    def set_prev_im(self, img):
        self.fixer.set_prev_im(img)
        return self.color_filter.set_prev_im(img)

    def get_prev_im(self):
        return self.color_filter.prev_im

    def update_board(self):
        self.color_filter.update_board()

    def get_board_test(self,is_before):
        if is_before:
            return self.color_filter.squares_before_test
        else:
            return self.color_filter.squares_after_test
