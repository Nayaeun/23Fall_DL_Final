#%%
import numpy as np
from PIL import Image
import os
import string
from pickle import dump
from pickle import load
from keras.applications.xception import Xception #to get pre-trained model Xception
from keras.applications.xception import preprocess_input
from keras.preprocessing.image import load_img
from keras.preprocessing.image import img_to_array
from keras.preprocessing.text import Tokenizer #for text tokenization
from keras.preprocessing.sequence import pad_sequences
from keras.utils import to_categorical
from keras.models import Model, load_model
from keras.layers import Input, Dense#Keras to build our CNN and LSTM
from keras.layers import LSTM, Embedding, Dropout, add
from keras.utils import plot_model
import argparse
from tqdm import tqdm #to check loop progress
tqdm().pandas()
#from dataclean import DataPreprocessor

# #%% Perform Data Cleaning
# # Load the document file into memory
# def load_fp(filename):
#     # Open file to read
#     file = open(filename, 'r')
#     text = file.read()
#     file.close()
#     return text
#
# # get all images with their captions
# def img_capt(filename):
#     file = load_fp(filename)
#     captions = file.split('\n')
#     descriptions = {}
#     for caption in captions[:-1]:
#         img, caption = caption.split('\t')
#         if img[:-2] not in descriptions:
#             descriptions[img[:-2]] = [caption]
#         else:
#             descriptions[img[:-2]].append(caption)
#     return descriptions
#
# # Data cleaning function will convert all upper case alphabets to lowercase, removing punctuations and words containing numbers
# def txt_clean(captions):
#     table = str.maketrans('', '', string.punctuation)
#     for img, caps in captions.items():
#         for i, img_caption in enumerate(caps):
#             img_caption = img_caption.replace("-", " ")
#             descp = img_caption.split()
#             # uppercase to lowercase
#             descp = [wrd.lower() for wrd in descp]
#             # remove punctuation from each token
#             descp = [wrd.translate(table) for wrd in descp]
#             # remove hanging 's and a
#             descp = [wrd for wrd in descp if (len(wrd) > 1)]
#             # remove words containing numbers with them
#             descp = [wrd for wrd in descp if (wrd.isalpha())]
#             # converting back to string
#             img_caption = ' '.join(descp)
#             captions[img][i] = img_caption
#
#     return captions
#
# def txt_vocab(descriptions):
#     # To build vocab of all unique words
#     vocab = set()
#     for key in descriptions.keys():
#         [vocab.update(d.split()) for d in descriptions[key]]
#     return vocab
#
# # To save all descriptions in one file
# def save_descriptions(descriptions, filename):
#     lines = list()
#     for key, desc_list in descriptions.items():
#         for desc in desc_list:
#             lines.append(key + '\t' + desc)
#     data = "\n".join(lines)
#     file = open(filename, "w")
#     file.write(data)
#     file.close()
#
# # # Set these path according to project folder in your system, like I created a folder with my name shikha inside D-drive
# dataset_text = "/home/ubuntu/DL/Dataset/Flicker8k_text"
# dataset_images = "/home/ubuntu/DL/Dataset/Flicker8k_Dataset"
#
# # to prepare our text data
# filename = dataset_text + "/" + "Flickr8k.token.txt"
#
# # loading the file that contains all data
# # map them into descriptions dictionary
# descriptions = img_capt(filename)
# print("Length of descriptions =", len(descriptions))
#
# # cleaning the descriptions
# clean_descriptions = txt_clean(descriptions)
#
# # to build vocabulary
# vocabulary = txt_vocab(clean_descriptions)
# print("Length of vocabulary =", len(vocabulary))
#
# # saving all descriptions in one file
# save_descriptions(clean_descriptions, "descriptions.txt")




#%%
import os
import string

class DataPreprocessor:
    def __init__(self, dataset_text, dataset_images, save_directory):
        self.dataset_text = dataset_text
        self.dataset_images = dataset_images
        self.save_directory = save_directory
        self.descriptions = None
        self.clean_descriptions = None
        self.vocabulary = None

    def load_fp(self, filename):
        file_path = os.path.join(self.dataset_text, filename)
        with open(file_path, 'r') as file:
            text = file.read()
        return text

    def img_capt(self, filename):
        file = self.load_fp(filename)
        captions = file.split('\n')
        descriptions = {}
        for caption in captions[:-1]:
            img, caption = caption.split('\t')
            if img[:-2] not in descriptions:
                descriptions[img[:-2]] = [caption]
            else:
                descriptions[img[:-2]].append(caption)
        return descriptions

    def txt_clean(self, captions):
        table = str.maketrans('', '', string.punctuation)
        for img, caps in captions.items():
            for i, img_caption in enumerate(caps):
                img_caption = img_caption.replace("-", " ")
                descp = img_caption.split()
                descp = [wrd.lower() for wrd in descp]
                descp = [wrd.translate(table) for wrd in descp]
                descp = [wrd for wrd in descp if (len(wrd) > 1)]
                descp = [wrd for wrd in descp if (wrd.isalpha())]
                img_caption = ' '.join(descp)
                captions[img][i] = img_caption
        return captions

    def txt_vocab(self, descriptions):
        vocab = set()
        for key in descriptions.keys():
            [vocab.update(d.split()) for d in descriptions[key]]
        return vocab

    def save_descriptions(self, descriptions, filename):
        lines = []
        for key, desc_list in descriptions.items():
            for desc in desc_list:
                lines.append(key + '\t' + desc)
        data = "\n".join(lines)
        file_path = os.path.join(self.save_directory, filename)
        with open(file_path, "w") as file:
            file.write(data)
    def preprocess_data(self, token_file="Flickr8k.token.txt", save_filename="descriptions.txt"):
        token_filepath = os.path.join(self.dataset_text, token_file)
        self.descriptions = self.img_capt(token_filepath)
        self.clean_descriptions = self.txt_clean(self.descriptions)
        self.vocabulary = self.txt_vocab(self.clean_descriptions)
        self.save_descriptions(self.clean_descriptions, save_filename)

dataset_text = "/home/ubuntu/DL/dataset/Flicker8k_text"
dataset_images = "/home/ubuntu/DL/dataset/Flicker8k_Dataset"
save_directory = "/home/ubuntu/DL/code"
preprocessor = DataPreprocessor(dataset_text, dataset_images, save_directory)
preprocessor.preprocess_data()

#%%
from torchvision import models, transforms
import torch

# Load the ResNet50 model pretrained on ImageNet
model = models.resnet50(pretrained=True)
model = torch.nn.Sequential(*(list(model.children())[:-1]))  # Remove the last fully connected layer
model.eval()

# Preprocess input image
def preprocess_image(image_path):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    image = Image.open(image_path).convert('RGB')
    image = transform(image)
    image = image.unsqueeze(0)  # Add batch dimension
    return image

# Extract features using ResNet50
def extract_features(directory):
    features = {}
    for pic in tqdm(os.listdir(directory)):
        file = os.path.join(directory, pic)
        try:
            image = preprocess_image(file)
            with torch.no_grad():
                feature = model(image)
            features[pic] = feature.squeeze().numpy()
        except Exception as e:
            print(f"Error processing image {file}: {e}")
    return features

# Example usage
features = extract_features(dataset_images)

# Save or use the features as needed
dump(features, open("features.p", "wb"))

# to directly load the features from the pickle file.
features = load(open("features.p", "rb"))


#=================================
# Print the keys (file names) in the features dictionary
print("Keys (File Names):", list(features.keys()))

# Print the shape of the features for the first image
first_image_key = list(features.keys())[0]
first_image_features = features[first_image_key]
print("Shape of Features for the First Image:", first_image_features.shape)

# Print the features for the first image
print("Features for the First Image:")
print(first_image_features)


# #%% # Extract the Feature Vector
# model = Xception(include_top=False, pooling='avg')
#
# def extract_features(directory):
#     model = Xception(include_top=False, pooling='avg')
#     features = {}
#
#     for pic in tqdm(os.listdir(directory)):
#         file = os.path.join (directory, pic)# directory + "/" + pic
#         try:
#             image = Image.open(file)
#             image = image.resize((299, 299))
#             image = np.expand_dims(image, axis=0)
#         # image = preprocess_input(image)
#             image = image / 127.5
#             image = image - 1.0
#             feature = model.predict(image)
#             features[pic] = feature
#         except Exception as e:
#             print (f"Error processing image {file}: {e}")
#
#     return features
#
# # 2048 feature vector
# features = extract_features(dataset_images)
# dump(features, open("features.p", "wb"))
# # to directly load the features from the pickle file.
# features = load(open("features.p", "rb"))

#%% Loading dataset for modeling training
# Load the document file into memory (assuming load_doc is defined elsewhere)
def load_photos(filename):
    file = preprocessor.load_fp(filename)
    photos = file.split("\n")[:-1]  # Using "\n" for newline
    return photos

# Load clean descriptions
def load_clean_descriptions(filename, photos):
    file = preprocessor.load_fp(filename)
    descriptions = {}

    for line in file.split("\n"):
        words = line.split()
        if len(words) < 1:
            continue
        image, image_caption = words[0], words[1:]

        if image in photos:
            if image not in descriptions:
                descriptions[image] = []
            desc = ' ' + " ".join(image_caption) + ' '
            descriptions[image].append(desc)

    return descriptions

# Load features
def load_features(photos):
    # Assuming load is defined elsewhere
    all_features = load(open("features.p", "rb"))
    features = {k: all_features[k] for k in photos}
    return features

filename_imgs = dataset_text + "/" + "Flickr_8k.trainImages.txt"
train_imgs = load_photos(filename_imgs)
train_descriptions = load_clean_descriptions("descriptions.txt", train_imgs)
train_features = load_features(train_imgs)


#%% # Tokenizing the Vocabulary
# # Convert dictionary to clear list of descriptions - original
# def dict_to_list(descriptions):
#     all_desc = []
#     for key in descriptions.keys():
#         [all_desc.append(d) for d in descriptions[key]]
#     return all_desc
#
# # Creating tokenizer class
# # This will vectorize the text corpus
# # Each integer will represent a token in the dictionary
# from keras.preprocessing.text import Tokenizer
#
# def create_tokenizer(descriptions):
#     desc_list = dict_to_list(descriptions)
#     tokenizer = Tokenizer()
#     tokenizer.fit_on_texts(desc_list)
#     return tokenizer
#
# # Give each word an index and store that into tokenizer.p pickle file
# tokenizer = create_tokenizer(train_descriptions)
# dump(tokenizer, open('tokenizer.p', 'wb'))
# vocab_size = len(tokenizer.word_index) + 1
# print("Vocabulary size:", vocab_size)
#
# # Calculate the maximum length of descriptions to decide the model structure parameters
# def max_length(descriptions):
#     desc_list = dict_to_list(descriptions)
#     return max(len(d.split()) for d in desc_list)
#
# max_length_value = max_length(train_descriptions)
# print("Max length of description:", max_length_value)


from transformers import BertTokenizer
import torch

class BertTextTokenizer:
    def __init__(self, model_name='bert-base-uncased', max_length=64):
        self.tokenizer = BertTokenizer.from_pretrained(model_name)
        self.max_length = max_length

    def dict_to_list(self, descriptions):
        all_desc = []
        for key in descriptions.keys():
            [all_desc.append(d) for d in descriptions[key]]
        return all_desc

    def tokenize_descriptions(self, descriptions):
        tokenized_descriptions = []
        for desc in descriptions:
            tokens = self.tokenizer.encode(desc, add_special_tokens=True, max_length=self.max_length, truncation=True)
            tokenized_descriptions.append(tokens)
        return tokenized_descriptions

    def tokenize_and_get_max_length(self, descriptions):
        desc_list = self.dict_to_list(descriptions)
        tokenized_desc_list = self.tokenize_descriptions(desc_list)
        max_length_value = max(len(tokens) for tokens in tokenized_desc_list)
        return max_length_value

    def get_vocab_size(self, descriptions):
        return len(self.tokenizer.vocab)

# Example Usage
# Assuming train_descriptions is already defined
bert_tokenizer = BertTextTokenizer()
max_length_value = bert_tokenizer.tokenize_and_get_max_length(train_descriptions)
vocab_size = bert_tokenizer.get_vocab_size(train_descriptions)
tokenizer = bert_tokenizer.tokenizer

print("Tokenizer:", tokenizer)
print("Vocabulary Size:", vocab_size)
print("Max length of description:", max_length_value)

#%% # Create a Data generator
# # Data generator, used by model.fit_generator() - original
# def data_generator(descriptions, features, tokenizer, max_length, vocab_size):
#     while 1:
#         for key, description_list in descriptions.items():
#             # Retrieve photo features
#             feature = features[key][0]
#             inp_image, inp_seq, op_word = create_sequences(tokenizer, max_length, description_list, feature, vocab_size)
#             yield [[inp_image, inp_seq], op_word]
#
# def create_sequences(tokenizer, max_length, desc_list, feature, vocab_size):
#     x_1, x_2, y = list(), list(), list()
#     # Move through each description for the image
#     for desc in desc_list:
#         # Encode the sequence
#         seq = tokenizer.texts_to_sequences([desc])[0]
#         # Divide one sequence into various X,y pairs
#         for i in range(1, len(seq)):
#             # Divide into input and output pair
#             in_seq, out_seq = seq[:i], seq[i]
#             # Pad input sequence
#             in_seq = pad_sequences([in_seq], maxlen=max_length)[0]
#             # Encode output sequence
#             out_seq = to_categorical([out_seq], num_classes=vocab_size)[0]
#             # Store
#             x_1.append(feature)
#             x_2.append(in_seq)
#             y.append(out_seq)
#     return np.array(x_1), np.array(x_2), np.array(y)
#
# # To check the shape of the input and output for your model
# [a, b], c = next(data_generator(train_descriptions, train_features, bert_tokenizer, max_length_value, vocab_size))
# print(a.shape, b.shape, c.shape)
# # ((47, 2048), (47, 32), (47, 7577))


#===================================yoni=================================
def data_generator(descriptions, features, tokenizer, max_length, vocab_size):
    while 1:
        for key, description_list in descriptions.items():
            # Retrieve photo features
            feature = features[key][0]
            inp_seq, op_word = create_sequences(tokenizer, max_length, description_list, vocab_size)
            inp_image = np.array([feature] * len(inp_seq))  # Repeat the image features for each description
            yield [inp_image, inp_seq], op_word


def create_sequences(tokenizer, max_length, desc_list, vocab_size):
    x_1, x_2, y = list(), list(), list()
    # Move through each description for the image
    for desc in desc_list:
        # Tokenize the sequence
        seq = tokenizer.tokenizer.encode(desc, add_special_tokens=True, max_length=max_length, truncation=True)

        # Divide one sequence into various X,y pairs
        for i in range(1, len(seq)):
            # Divide into input and output pair
            in_seq, out_seq = seq[:i], seq[i]

            # Pad input sequence
            in_seq = pad_sequences([in_seq], maxlen=max_length, padding='post')[0]

            # Encode output sequence
            out_seq = to_categorical([out_seq], num_classes=vocab_size)[0]

            # Store
            x_1.append(in_seq)
            x_2.append(out_seq)
            y.append(out_seq)
    return np.array(x_1), np.array(x_2), np.array(y)

# To check the shape of the input and output for your model
[a, b], c = next(data_generator(train_descriptions, train_features, bert_tokenizer, max_length_value, vocab_size))
print(a[0].shape, a[1].shape, b.shape, c.shape)


#%% Define the CNN-RNN model
# Define the captioning model
def define_model(vocab_size, max_length):
    # Features from the CNN model compressed from 2048 to 256 nodes
    inputs1 = Input(shape=(2048,))
    fe1 = Dropout(0.5)(inputs1)
    fe2 = Dense(256, activation='relu')(fe1)

    # LSTM sequence model
    inputs2 = Input(shape=(max_length,))
    se1 = Embedding(vocab_size, 256, mask_zero=True)(inputs2)
    se2 = Dropout(0.5)(se1)
    se3 = LSTM(256)(se2)

    # Merging both models
    decoder1 = add([fe2, se3])
    decoder2 = Dense(256, activation='relu')(decoder1)
    outputs = Dense(vocab_size, activation='softmax')(decoder2)

    # Merge it [image, seq] [word]
    model = Model(inputs=[inputs1, inputs2], outputs=outputs)
    model.compile(loss='categorical_crossentropy', optimizer='adam')

    # Summarize model
    print(model.summary())
    plot_model(model, to_file='model.png', show_shapes=True, show_layer_names=True)

    return model

# Example usage:
# vocab_size and max_length should be defined
# model = define_model(vocab_size, max_length)

#%% Training the Image Caption Generator model
# train our model
print('Dataset: ', len(train_imgs))
print('Descriptions: train=', len(train_descriptions))
print('Photos: train=', len(train_features))
print('Vocabulary Size:', vocab_size)
print('Description Length: ', max_length_value)


model = define_model(vocab_size, max_length_value)
epochs = 1
steps = len(train_descriptions)

# creating a directory named models to save our models
models_dir = "models"
if not os.path.exists(models_dir):
    os.mkdir(models_dir)
else:
    print(f"Directory '{models_dir}' already exists.")

for _ in range(epochs):
    generator = DataGenerator(train_descriptions, train_features, tokenizer, max_length_value, vocab_size)
    model.fit(generator, epochs=1, steps_per_epoch=steps, verbose=1)
    model.save(os.path.join(models_dir, f"model_{_}.h5"))


#%% # Testing the Image Caption Generator model
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from keras.models import load_model
from keras.applications.xception import Xception
from keras.preprocessing.sequence import pad_sequences
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences

# Load tokenizer
tokenizer = load(open("tokenizer.p", "rb"))

# Load pre-trained captioning model
model = load_model('models/model_9.h5')

# # Xception model for image feature extraction
# xception_model = Xception(include_top=False, pooling="avg")


# def extract_features(filename, model):
#     try:
#         image = Image.open(filename)
#     except:
#         print("ERROR: Can't open image! Ensure that the image path and extension are correct.")
#     image = image.resize((299, 299))
#     image = np.array(image)
#
#     # For 4 channels images, convert them into 3 channels
#     if image.shape[2] == 4:
#         image = image[..., :3]
#
#     image = np.expand_dims(image, axis=0)
#     image = image / 127.5
#     image = image - 1.0
#     feature = model.predict(image)
#     return feature


def word_for_id(integer, tokenizer):
    for word, index in tokenizer.word_index.items():
        if index == integer:
            return word
    return None


def generate_desc(model, tokenizer, photo, max_length):
    in_text = 'start'
    for _ in range(max_length):
        sequence = tokenizer.texts_to_sequences([in_text])[0]
        sequence = pad_sequences([sequence], maxlen=max_length)
        pred = model.predict([photo, sequence], verbose=0)
        pred = np.argmax(pred)
        word = word_for_id(pred, tokenizer)
        if word is None:
            break
        in_text += ' ' + word
        if word == 'end':
            break
    return in_text


#%% # Image path from command line argument
# img_path = args['image']
# Use argparse to get the image path from the command line
# parser = argparse.ArgumentParser()
# parser.add_argument('--image', type=str, required=True, help='path to the image')
# args = parser.parse_args()
#
# # Extract features from the image
# photo = extract_features(args.image, xception_model)
#
# # Generate caption
# description = generate_desc(model, tokenizer, photo, max_length_value)
# print("\nGenerated Caption:")
# print(description)
#
# # Display the image
# img = Image.open(args.image)
# plt.imshow(img)
# plt.show()

# Set the image path directly
image_path = "/home/ubuntu/DL"
image_filename = 'download.jpeg'

# Extract features from the image
photo = extract_features(image_path)
if image_filename in photo:
    # Assuming xception_model is already defined
    feature = photo[image_filename]

    # Generate caption
    description = generate_desc(model, tokenizer, feature, max_length_value)
    print("\nGenerated Caption:")
    print(description)

    # Display the image
    img = Image.open(os.path.join(image_path, image_filename))
    plt.imshow(img)
    plt.show()
else:
    print(f"Image {image_filename} not found in the specified directory.")

# # Generate caption
# description = generate_desc(model, tokenizer, photo, max_length_value)
# print("\nGenerated Caption:")
# print(description)
#
# # Display the image
# img = Image.open(image_path)
# plt.imshow(img)
# plt.show()

