from utils import create_input_files

if __name__ == '__main__':
    # Create input files (along with word map)
    json_path = '../data/interim/dataset_coco.json'
    img_folder = '../data/interim/'
    output_folder = '../data/processed'
    create_input_files(dataset='coco',
                       karpathy_json_path=json_path,
                       image_folder=img_folder,
                       captions_per_image=5,
                       min_word_freq=5,
                       output_folder=output_folder,
                       max_len=50)
