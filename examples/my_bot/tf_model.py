import numpy as np
import tensorflow as tf
from tensorflow.keras import keras as ks
from sklearn import datasets
import pandas as pd
import os

dir_path = 'train_data/easy/1541127583'

class TensorflowModel():
   def weight_variable(shape):
      initial = tf.truncated_normal(shape, stddev=0.1)
      return tf.Variable(initial)

   def bias_variable(shape):
      initial = tf.constant(0.1, shape=shape)
      return tf.Variable(initial)

   def conv2d(x, W):
      return tf.nn.conv2d(x, W, strides=[1,1,1,1], padding='SAME')

   def max_pool_2x2(x):
      return tf.nn.max_pool(x, ksize=[1, 2, 2, 1],
                            strides=[1,2,2,1], padding='SAME')
   def conv_layer( input, shape):
      W = weight_variable(shape)
      b = bias_variable(shape[3])
      return tf.nn.relu(conv2d(input, W) + b)

   def full_layer(input, size):
      in_size = int(input.get_shape()[1])
      W = weight_variable([in_size, size])
      b = bias_variable([size])
      return tf.matmul(input, W) + b
   
   def predict(x, y_true, w, b):
      y_pred = tf.matmul(w, tf.transpose(x)) + b
      return y_pred

   def get_loss(y_pred, y_true):
      loss = tf.reduce_mean(tf.square(y_true - y_pred))
      return loss

   def get_optimizer(y_pred, y_true):
      loss = get_loss(y_pred, y_true)
      optimizer = tf.train.GradientDescentOptimizer(0.5)
      train = optimizer.minimize(loss)
      return train

   def run_model(x_data, y_data):
      wb_ = []
      # Define placeholders and variables

      x = tf.placeholder(tf.float32, shape= [None, 3])
      y_true = tf.placeholder(tf.float32, shape = None)
      w = tf.Variable([[0,0,0]], dtype=tf.float32)
      b = tf.Variable(0, dtype=tf.float32)
      print(b.name)

      # Form predictions
      y_pred = predict(x, y_true, w, b)

      # Create Optimizer
      train = get_optimizer(y_pred, y_data)

      # Run session
      init = tf.global_variables_initializer()
      with tf.Session() as sess:
         sess.run(init)
         for step in range(10):
            sess.run(train, {x: x_data, y_true: y_data})
            if (step % 5 == 0):
               print(step, sess.run([w, b]))
               wb_.append(sess.run([w, b]))

   def main():
      c = tf.constant(5.0)
      print(c)



print(os.path.join())

boston_housing = keras.datasets.boston_housing

(train_data, train_labels), (test_data, test_labels) = boston_housing.load_data()

# Shuffle the training set
order = np.argsort(np.random.random(train_labels.shape))
train_data = train_data[order]
train_labels = train_labels[order]