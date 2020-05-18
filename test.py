import unittest

from imageio import imread

import src
from src.definitions import ROOT_DIR
from src.models.models import Encoder, DecoderWithAttention

class TestGeneratingCaptions(unittest.TestCase):

    def test_captions(self):
        word_map_file = ROOT_DIR/'data/processed'/'WORDMAP_coco_5_cap_per_img_5_min_word_freq.json'
        model = src.ImageCaptioner(word_map_file)
        model.init_model(ROOT_DIR/'models/ch1.pth.tar')

        # load image
        img_path = ROOT_DIR/'imgs/football.jpg'
        img = imread(img_path)
        sent = model.gen_caption(img)
        print(sent)


if __name__ == '__main__':
    unittest.main()

