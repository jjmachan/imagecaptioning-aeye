import json

from PIL import Image
import torch
import torchvision
from torchvision import transforms
import torch.nn.functional as F
from imageio import imread

from .models.models import Encoder, DecoderWithAttention
from .definitions import ROOT_DIR

class ImageCaptioner():
    """
    Class that generates the Captions from the pretrained model

    This class represents the Image Captioning Model as a whole since
    internally the there are 2 different models involved. Once is an
    encoder that enoders the image that is given and another is the
    decoder that generates the caption.

    Attributes
    ----------

    encoder : torch.nn
        Based on a ResNet model this encoder the image to create a
        vector representation that can be used by the decoder to ceate
        the caption.

    decoder : torch.nn
        This is an LSTM network with an attention layer that generates
        the caption with the vector representation generated by the
        encoder.

    word_map : dict
        Maps the words to their indices which is used to create their
        embeddings.

    rev_word_map : dict
        The reverse of word_map, maps the indices to the words. Used to
        get the final words form the indices the network predicts.

    beam_size : int
        We use beam search to improve accuracy of the captions generated
        This depth of the seach space.

    transform : torchvision.transforms
        The input image preprocessing steps before inputing the model
        to the decoder.

    Methods
    -------

    gen_caption(img)
        Generates the caption for the given image using beam search.

    """

    def init_model_with_checkpoint(self, checkpoint_path):

        # Define model
        # IMP: make sure the hyperparameters for the model is the same as
        # that in training.
        emb_dim = 512
        attention_dim = 512
        decoder_dim = 512
        dropout = 0.5
        word_map = self.word_map
        vocab_size = self.vocab_size

        decoder = DecoderWithAttention(attention_dim=attention_dim,
                                       embed_dim=emb_dim,
                                       decoder_dim=decoder_dim,
                                       vocab_size=vocab_size,
                                       dropout=dropout,)
        encoder = Encoder()

        # Initialize model
        # load to cpu
        cpu = torch.device('cpu')
        checkpoint = torch.load(checkpoint_path, map_location=cpu)
        decoder_state = checkpoint['decoder_state']
        encoder_state = checkpoint['encoder_state']
        decoder.load_state_dict(decoder_state)
        encoder.load_state_dict(encoder_state)

        self.encoder = encoder
        self.decoder = decoder

        return encoder, decoder

    def init_model_with_encoder_decoder(self, encoder, decoder):
        self.encoder = encoder
        self.decoder = decoder

    def __init__(self,
            word_map_file=None,
            checkpoint=None,
            encoder=None,
            decoder=None
            ):
        beam_size = 3
        with open(word_map_file, 'r') as file:
            self.word_map = json.load(file)
        self.vocab_size = len(self.word_map)
        self.rev_word_map = {v:key for key, v in self.word_map.items()}

        self.beam_size = beam_size

        self.transform = transforms.Compose([
           transforms.Resize(256),
           transforms.CenterCrop(224),
           transforms.ToTensor(),
           transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                std=[0.229, 0.224, 0.225]),
           ])

        if checkpoint is not None:
            assert encoder is None and decoder is None
            self.init_model_with_checkpoint(checkpoint)

        else:
            checkpoint is None
            self.init_model_with_encoder_decoder(encoder, decoder)

    def gen_caption(self, img):
        k = self.beam_size
        cpu = torch.device('cpu')

        # Get the image
        img = Image.fromarray(img)
        img = self.transform(img)
        # (3, 224, 224)
        img = img.unsqueeze(0)

        # Pass to encoder
        encoder = self.encoder.to(cpu)
        encoder.eval()
        # (1, enc_img_size, enc_img_size, encoder_dim)
        encoder_out = encoder(img)
        enc_img_size = encoder_out.size(1)
        encoder_dim = encoder_out.size(3)

        # (1, enc_img_size*enc_img_size, encoder_dim)
        encoder_out = encoder_out.view(1, -1, encoder_dim)
        num_pixels = encoder_out.size(1)

        # we are treating the problem as having a batch size of k
        encoder_out = encoder_out.expand(k, num_pixels, encoder_dim)

        # Tensor to store top k previous word at each step
        # (k, 1)
        k_prev_words = torch.LongTensor([[self.word_map['<start>']]] * k)

        # Tensor to store top k sequences; now they're just <start>
        # (k, 1)
        seqs = k_prev_words

        # Tensor to keep track of the scores of each seq
        top_k_scores = torch.zeros(k, 1)

        # list to store completed seqs and scores
        complete_seqs = list()
        complete_seqs_alpha = list()
        complete_seqs_scores = list()

        # Start decoding
        step = 1
        decoder = self.decoder.to(cpu)
        decoder.eval()
        h, c = decoder.init_hidden_state(encoder_out)

        # s is a number less than or equal to k, because sequences are removed
        # from this process once they hit <end>
        while True:

            # (s, embed_dim)
            embeddings = decoder.embedding(k_prev_words).squeeze(1)
            # (s, encoder_dim) (s, num_pixels)
            awe, _ = decoder.attention(encoder_out, h)


            # Gating scalar
            # (s, encoder_dim)
            gate = decoder.sigmoid(decoder.f_beta(h))
            awe = gate*awe

            # (s, decoder_dim)
            h, c = decoder.decode_step(torch.cat([embeddings, awe], dim=1), (h,c))

            # (s, vocab_size)
            scores = decoder.fc(h)
            scores = F.log_softmax(scores, dim=1)

            # Add
            scores = top_k_scores.expand_as(scores) + scores

            if step == 1:
                # if first step then all the words are same
                top_k_scores, top_k_words = scores[0].topk(k, 0, True, True)
            else:
                # else unroll and get the top k scores and word indexes
                top_k_scores, top_k_words = scores.view(-1).topk(k, 0, True, True)

            # convert the unrolled indices to actual indices of scores
            prev_word_inds = top_k_words / self.vocab_size
            next_word_inds = top_k_words % self.vocab_size

            # add words to sequence
            # (s, step+1)
            seqs = torch.cat([seqs[prev_word_inds], next_word_inds.unsqueeze(1)], dim=1)

            # the seq that did not reach <end>
            incomplete_inds = [ind for ind, next_word in enumerate(next_word_inds) if
                               next_word != self.word_map['<end>']]
            complete_inds = list(set(range(len(next_word_inds))) - set(incomplete_inds))

            # set aside complete sequences
            if len(complete_inds) > 0:
                complete_seqs.extend(seqs[complete_inds].tolist())
                complete_seqs_scores.extend(top_k_scores[complete_inds])
            k -= len(complete_inds)

            # Proceed with incomplete sequences
            if k == 0:
                break
            seqs = seqs[incomplete_inds]
            h = h[prev_word_inds[incomplete_inds]]
            c = c[prev_word_inds[incomplete_inds]]
            encoder_out = encoder_out[prev_word_inds[incomplete_inds]]
            top_k_scores = top_k_scores[incomplete_inds].unsqueeze(1)
            k_prev_words = next_word_inds[incomplete_inds].unsqueeze(1)

            # break if running for too long
            if step > 50:
                break
            step += 1

        i = complete_seqs_scores.index(max(complete_seqs_scores))
        seq = complete_seqs[i]

        print(seq)
        words = [self.rev_word_map[ind] for ind in seq]
        return ' '.join(words)

if __name__ == '__main__':
    word_map_file = ROOT_DIR/'data/processed'/'WORDMAP_coco_5_cap_per_img_5_min_word_freq.json'
    model = ImageCaptioner(word_map_file)
    model.init_model(ROOT_DIR/'models/best_checkpoint.pth.tar')

    # load image
    img_path = ROOT_DIR/'imgs/football.jpg'
    img = imread(img_path)
    sent = model.gen_caption(img)
    print(sent)
