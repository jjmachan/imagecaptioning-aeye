# Download files
# MS-COCO Dataset
coco_train=http://images.cocodataset.org/zips/train2014.zip
coco_train_file=data/raw/coco_train.zip
coco_val=http://images.cocodataset.org/zips/val2014.zip
coco_val_file=data/raw/coco_val.zip

# Caption file
caption_file=http://cs.stanford.edu/people/karpathy/deepimagesent/caption_datasets.zip

echo Starting Download script
#wget $coco_train -O $coco_train_file
#wget $coco_val -O $coco_train_file
#wget $caption_file -O data/raw/captions.zip

echo Finished data downloads
echo Extracting data to interim...

train_folder=data/interim/train
test_folder=data/interim/test
val_folder=data/interim/val

if [ ! -d "$train_folder" ]; then
  echo "interim dirs not found. Creating..."
  mkdir $train_folder
fi

if [ ! -d $test_folder ]; then
  mkdir $test_folder
fi

if [ ! -d $val_folder ]; then
  mkdir $val_folder
fi

src_dir=''
dest_dir=''
large_cp()
{       
        echo "coping files $src_dir /* -> $dest_dir" 
        while read line1; do
                cp $src_dir/$line1 $dest_dir
        done
}

# unzip files to dir
unzip $coco_train_file -d $train_folder

# moving large number of folders
src_dir=data/interim/train/train2014
dest_dir=data/interim/train/
ls -1 data/interim/train/train2014 | large_cp
rm -r data/interim/train/train2014

unzip $coco_val_file -d $val_folder

src_dir=data/interim/val/val2014
dest_dir=data/interim/val
ls -1 data/interim/val/val2014 | large_cp

rm -r data/interim/val/val2014/
