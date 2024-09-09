import os
import numpy as np
import tensorflow as tf

from data_generator import DataGenerator
from dotenv import load_dotenv


"""
The following demotrates how to use the DataGenerator class to train,
validate, and test a model in tensorflow.
"""

load_dotenv()
USER = os.getenv('POSTGRES_USER')
PASSWORD = os.getenv('POSTGRES_PASSWORD')

# Create data generator
train_gen = DataGenerator(USER,PASSWORD)
train_gen.summary()

# Split the training data generator into validation, and test data generators
val_gen = train_gen.train_test_split(0.3)
val_gen.summary()

test_gen = val_gen.train_test_split(0.5, shuffle=False)
test_gen.summary()

train_gen.summary()

# Create categorical feature
category_input = tf.keras.layers.Input(shape=(1,), name='categories', dtype='int64')
x = tf.keras.layers.Hashing(num_bins=16, output_mode='one_hot')(category_input)

# Create price feature
price_input = tf.keras.Input(shape=(1,), name='prices')
disc_layer = tf.keras.layers.Discretization(num_bins=16, output_mode='one_hot')
disc_layer.adapt(train_gen.get_prices())
y = disc_layer(price_input)

# Create sequence feature
sequence_input = tf.keras.Input(shape=(None,12,), name='sequences')
z = tf.keras.layers.LSTM(16, return_sequences=False)(sequence_input)
z = tf.keras.layers.Dropout(0.2)(z)

# Concatenate features
w = tf.keras.layers.Concatenate()([x,y,z])

# Hidden layer
w = tf.keras.layers.Dense(256, activation='relu')(w)
w = tf.keras.layers.Dropout(0.2)(w)

# Make prediction
pred = tf.keras.layers.Dense(1, activation='relu')(w)

# Create model
model = tf.keras.Model(
	inputs=[category_input,price_input,sequence_input],
	outputs=pred
)
model.summary()

# Compile and fit
model.compile(optimizer='adam', loss='mse')
model.fit(
    x=train_gen,
    epochs=1,
    batch_size=train_gen.batch_size,
    validation_data=val_gen,
    validation_batch_size=val_gen.batch_size
)

# Evaluate model performance
model.evaluate(test_gen)