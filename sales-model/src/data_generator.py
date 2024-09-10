import random
import numpy as np
import pandas as pd
import tensorflow as tf


class DataGenerator(tf.keras.utils.PyDataset):

    """
    DataGenerator generates and preprocesses batches of data from sales and
    item csv files.
    """
    
    def __init__(
            self,
            sales_path=None,
            items_path=None,
            data='auto',
            ids=None,
            batch_size=32,
            seq_len=33,
            shuffle=True,
            seed=0,
            **krwags
        ):
        """
        Args:
            sales_path: The path to the sales csv file.
            items_path: The path to the items csv file.
            data: If set to auto, the data is loaded and preprocessed from
                the sales and items csv files. Otherwise, data is set with
                a dictionary of preprocessed dataframes.
            ids: If data is set to auto, the ids are the unique shop and item
                id pairs from the sales csv. Otherwise, ids is set with a
                list of shop and item id pairs.
            batch_size: The size of each batch of data. If the number of
                ids is not a multiple of the batch size, the last batch is 
                smaller.
            seq_len: The length of each sequence of monthly sales data.
            shuffle: If True, shuffles the data with seed value.
            seed: Seed value used to shuffle data.
        """
        super().__init__(**krwags)

        if (data == 'auto'):
            # Load sales data
            sales_df = pd.read_csv(sales_path)

            # Load item categories
            items_df = pd.read_csv(
                items_path,
                usecols=['item_id', 'item_category_id'],
                index_col=['item_id']
            )

            # Group item prices
            prices_df = sales_df[['shop_id', 'item_id', 'item_price']]
            prices_df = prices_df.groupby(
                by=['shop_id', 'item_id']
            ).agg('mean')

            # Group item count
            sales_df.drop(columns=['date', 'item_price'], inplace=True)
            sales_df = sales_df.groupby(
                by=['shop_id', 'item_id', 'date_block_num']
            ).agg('sum')

            # Store data
            self.data = {
                'sales': sales_df,
                'categories': items_df,
                'prices': prices_df
            }
        else:
            # Store data
            self.data = data      

        if not(ids):
            # Store unique shop and item id pairs
            ids = self.data['sales'].index.droplevel('date_block_num')
            self.ids = list(ids.unique())
        else:
            self.ids = ids
        
        self.shuffle = shuffle
        self.seed = seed

        # Shuffle data
        if (shuffle):
            random.seed(seed)
            random.shuffle(self.ids)
        
        self.batch_size = batch_size
        self.seq_len = seq_len
        
    def __len__(self):
        """ Returns the number of batches. """
        return np.ceil(len(self.ids) / self.batch_size).astype('int32')
    
    def __getitem__(self, idx):
        """ Gets the idx'th batch of data. """
        low = idx * self.batch_size
        high = min((idx + 1)* self.batch_size, len(self.ids))
        num_samples = high - low
        x_batch = {
            'sales': np.zeros((num_samples, self.seq_len, 12), dtype='float32'),
            'categories': np.empty(num_samples, dtype='int32'),
            'prices': np.empty(num_samples, dtype='float32')
        }
        y_batch = np.empty(num_samples)

        for i, (shop_id, item_id) in enumerate(self.ids[low:high]):
            # Add category id to batch
            x_batch['categories'][i] = self.data['categories'].loc[item_id]

            # Add max price to batch
            x_batch['prices'][i] = self.data['prices'].loc[(shop_id, item_id)]

            # Create sales sequence
            sales = self.data['sales'].loc[shop_id, item_id,:]
            seq = np.zeros((self.seq_len+1,12))
            for date_block_num, item_cnt in sales.itertuples():
                seq[date_block_num, date_block_num%12] += item_cnt
            
            # Add sequence to x and y batch
            x_batch['sales'][i] = seq[:-1]
            y_batch[i] = np.sum(seq[-1])

        return x_batch, y_batch
    
    def train_test_split(self, frac=0.2, shuffle=True, seed=0):
        """
        Removes a fraction of the data from the data generator, and returns a
        new DataGenerator with the removed data and the same attributes. If 
        shuffle is set to False, train_test_split removes and adds the last 
        data points from the data generator.
        """
        sample_ids = []
        num_samples = int(frac * len(self.ids))
        # Sample ids
        if (shuffle):
            # Remove and add the ids randomly from the data generator
            random.seed(seed)
            for i in reversed(range(len(self.ids)-num_samples,len(self.ids))):
                sample_ids.append(self.ids.pop(random.randrange(i)))
        else:
            # Remove and add the last ids from the data generator
            for i in range(num_samples):
                sample_ids.append(self.ids.pop())

        return DataGenerator(
            data=self.data,
            ids=sample_ids,
            batch_size=self.batch_size,
            seq_len=self.seq_len,
            shuffle=self.shuffle,
            seed=self.seed
        )
    
    def get_prices(self):
        """ Gets all of the item prices from the database. """
        prices = np.array(self.data['prices'].loc['item_price'])
        return np.squeeze(prices)
    
    def head(self, n=5):
        """ Return the first n rows. """
        head = {}
        for key, value in self.data.items():
            head[key] = value.head(n)
        return head