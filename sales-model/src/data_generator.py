import random
import numpy as np
import pandas as pd
import tensorflow as tf


class DataGenerator(tf.keras.utils.PyDataset):

    """
    DataGenerator generates and preprocesses batches of data.
    """
    
    def __init__(
            self,
            sales_data,
            items_data,
            batch_size=32,
            seq_len=33,
            shuffle=True,
            seed=0,
            **krwags
        ):
        """
        Args:
            sales_data: The path to the sales csv file.
            items_data: The path to the items csv file.
            batch_size: The size of each batch of data. If the number of
                ids is not a multiple of the batch size, the last batch is 
                smaller.
            seq_len: The length of each sequence of monthly sales data.
            shuffle: If True, shuffles the data with seed value.
            seed: Seed value used to shuffle data.
        """
        super().__init__(**krwags)

        sales_df = pd.read_csv(sales_data)
        items_df = pd.read_csv(
            items_data,
            usecols=['item_id', 'item_category_id'],
            index_col=['item_id']
        )

        # Join sales_df with item_df on item_id
        sales_df = sales_df.join(items_df, on='item_id')

        # Convert date column to datetime type
        sales_df['date'] = pd.to_datetime(sales_df['date'], format='%d.%m.%Y')

        # Aggregate date by shop_id, item_id, and date
        agg_funcs = {
            'date_block_num':'max',
            'item_category_id':'min',
            'item_price':'mean',
            'item_cnt_day':'sum'
        }
        sales_df = sales_df.groupby(by=['shop_id', 'item_id', 'date']).agg(agg_funcs)

        # Store sales_df as data
        self.data = sales_df

        # Store unique shop and item id pairs as ids
        self.ids = list(sales_df.index.droplevel('date').unique())

        self.shuffle = shuffle

        # Shuffle data
        if (shuffle):
            self.seed = seed
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
            'categories': np.empty(num_samples, dtype='int32'),
            'prices': np.empty(num_samples, dtype='float32'),
            'sequences': np.zeros((num_samples, self.seq_len, 12), dtype='float32')
        }
        y_batch = np.empty(num_samples)

        for i, id in enumerate(self.ids[low:high]):
            # Get all data
            data = self.data.loc[id,:]

            # Add category id to batch
            x_batch['categories'][i] = data.pop('item_category_id').min()

            # Add max price to batch
            x_batch['prices'][i] = data.pop('item_price').max()

            # Create sales sequence
            seq = np.zeros((self.seq_len+1,12))
            for date, date_block_num, item_cnt in data.itertuples():
                seq[date_block_num, date.month-1] += item_cnt
            
            # Add sequence to x and y batch
            x_batch['sequences'][i] = seq[:-1]
            y_batch[i] = np.sum(seq[-1])

        return x_batch, y_batch
    
    def train_test_split(self, frac=0.2, shuffle=True, seed=0):
        """
        Removes a fraction of the data from the data generator, and returns a
        new DataGenerator with the removed data and the same attributes. If 
        shuffle is set to False, train_test_split removes and adds the last 
        data points from the data generator.
        """
        ids = []
        num_samples = int(frac * len(self.ids))
        # Sample ids
        if (shuffle):
            # Remove and add the ids randomly from the data generator
            random.seed(seed)
            for i in reversed(range(len(self.ids) - num_samples, len(self.ids))):
                ids.append(self.ids.pop(random.randrange(i)))
        else:
            # Remove and add the last ids from the data generator
            for i in range(num_samples):
                ids.append(self.ids.pop())
        
        return DataGenerator(
            ids=ids,
            sales_db=self.sales_db,
            batch_size=self.batch_size,
            seq_len=self.seq_len,
            shuffle=self.shuffle,
            seed=self.seed
        )
    
    def get_prices(self):
        """ Gets all of the item prices from the database. """
        prices = np.array(self.sales_db.getPrices(), dtype='float32')
        return np.squeeze(prices)
    
    def head(self):
        """  """
        return self.data.head()