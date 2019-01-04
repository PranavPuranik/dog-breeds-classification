from keras.layers import Conv2D, MaxPooling2D, GlobalAveragePooling2D
from keras.layers import Dropout, Flatten, Dense
from keras.models import Sequential
from keras.models import model_from_json

import cv2

from keras.applications.resnet50 import preprocess_input, decode_predictions
from keras.preprocessing import image                  
from tqdm import tqdm
from keras.applications.resnet50 import ResNet50
from extract_bottleneck_features import *

import numpy as np
import os

LABELS_PATH = os.path.abspath('dog_names.txt')

with open(LABELS_PATH) as f:
    labels = f.readlines()

dog_names = np.array([label.strip() for label in labels])

# Extract pre-trained face detector
face_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_alt.xml')

# returns "True" if face is detected in image stored at img_path
def face_detector(img_path):
    img = cv2.imread(img_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray)
    return len(faces) > 0

# define ResNet50 model
ResNet50_model = ResNet50(weights='imagenet')

def path_to_tensor(img_path):
    # loads RGB image as PIL.Image.Image type
    img = image.load_img(img_path, target_size=(224, 224))
    # convert PIL.Image.Image type to 3D tensor with shape (224, 224, 3)
    x = image.img_to_array(img)
    # convert 3D tensor to 4D tensor with shape (1, 224, 224, 3) and return 4D tensor
    return np.expand_dims(x, axis=0)

def paths_to_tensor(img_paths):
    list_of_tensors = [path_to_tensor(img_path) for img_path in tqdm(img_paths)]
    return np.vstack(list_of_tensors)
    
def ResNet50_predict_labels(img_path):
    # returns prediction vector for image located at img_path
    img = preprocess_input(path_to_tensor(img_path))
    return np.argmax(ResNet50_model.predict(img))

def dog_detector(img_path):
    # Detect if an image has a dog or not
    prediction = ResNet50_predict_labels(img_path)
    return ((prediction <= 268) & (prediction >= 151)) 

### Define VGG19_model architecture.
with open('saved_models/VGG19_model.json', 'r') as json_file:
    loaded_model_json = json_file.read()

VGG19_model = model_from_json(loaded_model_json)

### TODO: Load the model weights with the best validation loss.
VGG19_model.load_weights('saved_models/weights.best.VGG19.hdf5')

# compile and evaluate loaded model
VGG19_model.compile(loss='categorical_crossentropy', optimizer='rmsprop', metrics=['accuracy'])

    
### Take a path to an image as input
### and returns the dog breed that is predicted by the model.
def VGG19_predict_breed(img_path):
    # extract bottleneck features
    bottleneck_feature = extract_VGG19(path_to_tensor(img_path))
    # obtain predicted vector
    predicted_vector = VGG19_model.predict(bottleneck_feature)
    # return dog breed that is predicted by the model
    return dog_names[np.argmax(predicted_vector)]
    
def dog_breed_pred(path):
    # Detect dog or human and run prediction
    if dog_detector(path):
        dog_breed = VGG19_predict_breed(path)
        result = 'This dog looks like a ' + dog_breed + '.'
    elif face_detector(path):
        resemb_dog_breed = VGG19_predict_breed(path)
        result = 'The most resembling dog breed of this person is ' + resemb_dog_breed + '.'
    else:
        result = 'There is no human or dog detected in this picture.'
    return result
    
print (dog_breed_pred('images/Chihuahua.jpg'))
print (dog_breed_pred('images/bird.jpg'))
print (dog_breed_pred('images/Shuo.jpg'))