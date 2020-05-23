import unittest

from imageio import imread

import imagecaptioning
from imagecaptioning.definitions import ROOT_DIR

class TestGeneratingCaptions(unittest.TestCase):
    def test_captions(self):
        word_map_file = ROOT_DIR/'data/processed'/'WORDMAP_coco_5_cap_per_img_5_min_word_freq.json'
        checkpoint = ROOT_DIR/'models/best_checkpoint_only_state_dict.pth.tar'
        model = imagecaptioning.ImageCaptioner(word_map_file=word_map_file,
                                               checkpoint=checkpoint)

        # load image
        img_path = ROOT_DIR/'imgs/football.jpg'
        img = imread(img_path)
        sent = model.gen_caption(img)
        print(sent)

        # extract encoder and decoder
        self.encoder = model.encoder
        self.decoder = model.decoder

    def test_caption_with_encoder_decoder(self):

        word_map_file = ROOT_DIR/'data/processed'/'WORDMAP_coco_5_cap_per_img_5_min_word_freq.json'
        checkpoint = ROOT_DIR/'models/best_checkpoint_only_state_dict.pth.tar'
        model = imagecaptioning.ImageCaptioner(word_map_file=word_map_file,
                                               checkpoint=checkpoint)

        # init new model from encoder and decoder
        model_from_encoder_decoder = imagecaptioning.ImageCaptioner(
                                                word_map_file=word_map_file,
                                                encoder=model.encoder,
                                                decoder=model.decoder)

        # load_img
        img_path = ROOT_DIR/'imgs/football.jpg'
        img = imread(img_path)
        sent = model_from_encoder_decoder.gen_caption(img)
        print(sent)

if __name__ == '__main__':
    unittest.main()

