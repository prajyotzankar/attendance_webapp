import csv
import cv2
import numpy as np
import os
import sys
import re
import time
from PIL import Image
import tensorflow as tf
from keras.models import load_model
from keras.preprocessing.image import img_to_array
from keras.preprocessing.image import load_img
from lxml import etree
from matplotlib import pyplot
from matplotlib.patches import Rectangle
from numpy import expand_dims
from tensorflow.keras import backend as K



class BoundBox:
    def __init__(self, xmin, ymin, xmax, ymax, objness = None, classes = None):
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax
        self.objness = objness
        self.classes = classes
        self.label = -1
        self.score = -1
        
    def get_label(self):
        if self.label == -1:
            self.label = np.argmax(self.classes)
        
        return self.label
    
    def get_score(self):
        if self.score == -1:
            self.score = self.classes[self.get_label()]
        
        return self.score


def _sigmoid(x):
    return 1. / (1. + np.exp(-x))



def decode_netout(netout, anchors, obj_thresh, net_h, net_w):
    grid_h, grid_w = netout.shape[:2] # 0 and 1 is row and column 13*13
    nb_box = 3 # 3 anchor boxes
    netout = netout.reshape((grid_h, grid_w, nb_box, -1)) #13*13*3 ,-1
    nb_class = netout.shape[-1] - 5
    boxes = []
    netout[..., :2]  = _sigmoid(netout[..., :2])
    netout[..., 4:]  = _sigmoid(netout[..., 4:])
    netout[..., 5:]  = netout[..., 4][..., np.newaxis] * netout[..., 5:]
    netout[..., 5:] *= netout[..., 5:] > obj_thresh
    
    for i in range(grid_h*grid_w):
        row = i / grid_w
        col = i % grid_w
        for b in range(nb_box):
            # 4th element is objectness score
            objectness = netout[int(row)][int(col)][b][4]
            if(objectness.all() <= obj_thresh): continue
            # first 4 elements are x, y, w, and h
            x, y, w, h = netout[int(row)][int(col)][b][:4]
            x = (col + x) / grid_w # center position, unit: image width
            y = (row + y) / grid_h # center position, unit: image height
            w = anchors[2 * b + 0] * np.exp(w) / net_w # unit: image width
            h = anchors[2 * b + 1] * np.exp(h) / net_h # unit: image height
            # last elements are class probabilities
            classes = netout[int(row)][col][b][5:]
            box = BoundBox(x-w/2, y-h/2, x+w/2, y+h/2, objectness, classes)
            boxes.append(box)
    return boxes


def correct_yolo_boxes(boxes, image_h, image_w, net_h, net_w):
    new_w, new_h = net_w, net_h
    for i in range(len(boxes)):
        x_offset, x_scale = (net_w - new_w)/2./net_w, float(new_w)/net_w
        y_offset, y_scale = (net_h - new_h)/2./net_h, float(new_h)/net_h
        boxes[i].xmin = int((boxes[i].xmin - x_offset) / x_scale * image_w)
        boxes[i].xmax = int((boxes[i].xmax - x_offset) / x_scale * image_w)
        boxes[i].ymin = int((boxes[i].ymin - y_offset) / y_scale * image_h)
        boxes[i].ymax = int((boxes[i].ymax - y_offset) / y_scale * image_h)


def _interval_overlap(interval_a, interval_b):
    x1, x2 = interval_a
    x3, x4 = interval_b
    if x3 < x1:
        if x4 < x1:
            return 0
        else:
            return min(x2,x4) - x1
    else:
        if x2 < x3:
            return 0
        else:
            return min(x2,x4) - x3

#intersection over union        
def bbox_iou(box1, box2):
    intersect_w = _interval_overlap([box1.xmin, box1.xmax], [box2.xmin, box2.xmax])
    intersect_h = _interval_overlap([box1.ymin, box1.ymax], [box2.ymin, box2.ymax])
    intersect = intersect_w * intersect_h
    
    
    w1, h1 = box1.xmax-box1.xmin, box1.ymax-box1.ymin  
    w2, h2 = box2.xmax-box2.xmin, box2.ymax-box2.ymin
    
    #Union(A,B) = A + B - Inter(A,B)
    union = w1*h1 + w2*h2 - intersect
    return float(intersect) / union


def do_nms(boxes, nms_thresh):    #boxes from correct_yolo_boxes and  decode_netout
    if len(boxes) > 0:
        nb_class = len(boxes[0].classes)
    else:
        return
    for c in range(nb_class):
        sorted_indices = np.argsort([-box.classes[c] for box in boxes])
        for i in range(len(sorted_indices)):
            index_i = sorted_indices[i]
            if boxes[index_i].classes[c] == 0: continue
            for j in range(i+1, len(sorted_indices)):
                index_j = sorted_indices[j]
                if bbox_iou(boxes[index_i], boxes[index_j]) >= nms_thresh:
                    boxes[index_j].classes[c] = 0


# load and prepare an image
def load_image_pixels(filename, shape):
    # load the image to get its shape
    image = load_img(filename) #load_img() Keras function to load the image .
    width, height = image.size
    # load the image with the required size
    image = load_img(filename, target_size=shape) # target_size argument to resize the image after loading
    # convert to numpy array
    image = img_to_array(image)
    # scale pixel values to [0, 1]
    image = image.astype('float32')
    image /= 255.0  #rescale the pixel values from 0-255 to 0-1 32-bit floating point values.
    # add a dimension so that we have one sample
    image = expand_dims(image, 0)
    return image, width, height


# get all of the results above a threshold
def get_boxes(boxes, labels, thresh):
    v_boxes, v_labels, v_scores = list(), list(), list()
    # enumerate all boxes
    for box in boxes:
        # enumerate all possible labels
        for i in range(len(labels)):
            # check if the threshold for this label is high enough
            if box.classes[i] > thresh:
                v_boxes.append(box)
                v_labels.append(labels[i])
                v_scores.append(box.classes[i]*100)
    
    return v_boxes, v_labels, v_scores

def prewhiten(x):
    mean = np.mean(x)
    std = np.std(x)
    std_adj = np.maximum(std, 1.0/np.sqrt(x.size))
    y = np.multiply(np.subtract(x, mean), 1/std_adj)
    return y 

def to_rgb(img):
    w, h = img.shape
    ret = np.empty((w, h, 3), dtype=np.uint8)
    ret[:, :, 0] = ret[:, :, 1] = ret[:, :, 2] = img
    return ret

#crop the faces and save them as individual images
def crop_out_faces(input_file, filename, v_boxes, v_labels, v_scores):
    #load the image
    image = cv2.imread(input_file)
    images_names = []
    images_array = np.zeros((1, 160, 160, 3))
    for i in range(len(v_boxes)):

        box = v_boxes[i]
        # get coordinates
        y1, x1, y2, x2 = box.ymin, box.xmin, box.ymax, box.xmax
        #crop out face
        cropped_face = image[y1:y2, x1:x2]
        
        #save the image
        path_out = os.path.abspath('media\cropped_images')
        output = ""+filename.rsplit(".")[0]+'_face_'+str(i)+'.jpg'
        path_out = os.path.join(path_out, output)
        
        #cv2.imwrite(output,cropped_face)
        height = cropped_face.shape[0]
        width = cropped_face.shape[1]
        if width > 0 and height > 0:
            cv2.imwrite(path_out,cropped_face)
            image_array = np.zeros((1, 160, 160, 3))
            if cropped_face.ndim == 2:
                cropped_face = to_rgb(cropped_face)
            
            cropped_face = prewhiten(cropped_face)
            cropped_face = cv2.resize(cropped_face, (160, 160))
            image_array[0,:,:,:] = cropped_face
            images_array = np.vstack((images_array, image_array))
            images_names.append(output)
        else:
            print(width, height)

    return images_array[1:, : , : , :], images_names


def face_detection(model, input_file, image_in):
    
    # define the anchors
    anchors = [[116,90, 156,198, 373,326], [30,61, 62,45, 59,119], [10,13, 16,30, 33,23]]  

    # define the probability threshold for detected objects
    class_threshold = 0.8

    #define labels, in this case only face
    labels = ["face"]

    #define input size
    input_w, input_h = 416, 416
    
    image, image_w, image_h = load_image_pixels(input_file, (input_w, input_h))
    #print(image.shape)

    #detect the faces
    faces_detected = model.predict(image)

    #decode the output/predictions from the model
    boxes = []
    for i in range(len(faces_detected)):
        boxes += decode_netout(faces_detected[i][0], anchors[i], class_threshold, input_h, input_w)


    correct_yolo_boxes(boxes, image_h, image_w, input_h, input_w)

    #suppress non-maximal boxes
    #Discard all boxes with pc less or equal to 0.5
    do_nms(boxes, 0.5)  

    # get the details of the detected objects
    v_boxes, v_labels, v_scores = get_boxes(boxes, labels, class_threshold)
    
    #filename = input_file.split("/")[-1]
    filename =  re.split(r"/|\\", input_file)[-1]
    #uncomment this to debug/demo
    #create_annoted_image(input_file, filename, v_boxes, v_labels, v_scores)
    images_array, images_names = crop_out_faces(input_file, filename, v_boxes, v_labels, v_scores)
    #file_and_voc_xml_annot(input_file, filename, v_boxes, v_labels)
    return images_array, images_names

def face_detection_main(input_file):
    
    with tf.Graph().as_default():
        model = load_model("media/ml_models/face_detection_v1.h5")
        #check if the file exists
        if not os.path.isfile(input_file):
            print("[!] ==> Input image file {} doesn't exist".format(input_file))
            sys.exit(1)

        #get the File extension jpg, png, mp4.
        file_extension = input_file.split(".")[-1]
        print(file_extension)
        

        image_extensions = ['jpg', 'jpeg', 'png']
        video_extensions = ['mp4', 'mkv', 'm4v']
        
        #if input file is image then,
        if file_extension in image_extensions:
            ts = time.time()
            image = cv2.imread(input_file)
            face_detection(model, input_file, image)
            print(time.time() - ts)
        
        #if input file is video file then,
        elif file_extension in video_extensions:
            images_array_out = np.zeros((1, 160, 160, 3))
            images_names_out = []
            # Create a VideoCapture object and read from input file
            vidcap = cv2.VideoCapture(input_file)
            
            path_out = os.path.abspath('media')
            path_out = os.path.join(path_out, "video_frames")

            try:
                os.mkdir(path_out)
            except OSError as error:
                pass
            
            count = 0
            success,image = vidcap.read()
            success = True
            while success:
                ts = time.time()
                vidcap.set(cv2.CAP_PROP_POS_MSEC,(count*1000))  
                success,image = vidcap.read()
                if not success:
                    break
                image_path = path_out + "\\frame%d.jpg" % count
                cv2.imwrite(image_path, image)
                
                image_in = cv2.imread(image_path)
                images_array, images_names = face_detection(model, image_path, image_in)
                images_array_out = np.vstack((images_array_out, images_array))
                images_names_out += images_names
                os.remove(image_path)
                count = count + 1
                print(time.time() - ts)
            for f in os.listdir(path_out):
                os.remove(os.path.join(dir, f))   
            vidcap.release()
        
        
        return images_array_out[1:, : , : , :], images_names_out

