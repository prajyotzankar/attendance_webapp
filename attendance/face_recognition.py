import tensorflow as tf
import numpy as np
import argparse
from .facenet import load_model
import os
import sys
import math
import pickle
from sklearn.svm import SVC
from math import ceil
import time

def face_recognition_classsify(images_array, images_names, model_dir, classifier_filename_exp):
    
    ts = time.time()
    with tf.Graph().as_default():
        with tf.compat.v1.Session() as sess:
            
            present_students_PRN = []
            batch_size = 100
            nrof_images = images_array.shape[0]
            no_of_batches = ceil(nrof_images/batch_size)

            # Load the model
            print('Loading feature extraction model')
            load_model(model_dir)
            
            print('Testing classifier')
            with open(classifier_filename_exp, 'rb') as infile:
                (model, class_names) = pickle.load(infile)

            print('Loaded classifier model from file "%s"' % classifier_filename_exp)

            # Get input and output tensors
            images_placeholder = tf.compat.v1.get_default_graph().get_tensor_by_name("input:0")
            embeddings = tf.compat.v1.get_default_graph().get_tensor_by_name("embeddings:0")
            phase_train_placeholder = tf.compat.v1.get_default_graph().get_tensor_by_name("phase_train:0")
            embedding_size = embeddings.get_shape()[1]

            # Run forward pass to calculate embeddings
            print('Calculating features for images')
            emb_array = np.zeros((nrof_images, embedding_size))
            print("loading", time.time() - ts)
            for batch_no in range(no_of_batches):
                start_index = batch_size*batch_no
                if batch_no == no_of_batches - 1:
                    end_index = nrof_images - start_index
                else:
                    end_index = start_index + batch_size

                images_arrat_input = images_array[start_index:end_index]
                feed_dict = { images_placeholder:images_arrat_input, phase_train_placeholder:False }
                emb_array[start_index:end_index,:] = sess.run(embeddings, feed_dict=feed_dict)

                print("for loop", batch_no, time.time() - ts)
            
            # Classify images
            predictions = model.predict_proba(emb_array)
            best_class_indices = np.argmax(predictions, axis=1)
            best_class_probabilities = predictions[np.arange(len(best_class_indices)), best_class_indices]

            for i in range(len(best_class_indices)):
                student_name = class_names[best_class_indices[i]]
                if best_class_probabilities[i] >= 0.1 and \
                    student_name not in present_students_PRN:
                    present_students_PRN.append(student_name)

            
                
    return present_students_PRN
