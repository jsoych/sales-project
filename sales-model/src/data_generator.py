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
            batches='auto',
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
            batches: If set to auto, the data is loaded, preprocessed, and
                batched from the sales and items csv files. Otherwise, batches
                is set with a list of batches.
            batch_size: The size of each batch of data. If the number of
                ids is not a multiple of the batch size, the last batch is 
                smaller.
            seq_len: The length of each sequence of monthly sales data.
            shuffle: If True, shuffles the data with seed value.
            seed: Seed value used to shuffle data.
        """
        super().__init__(**krwags)

        self.batch_size = batch_size
        self.seq_len = seq_len

        # Batch data
        if (batches == 'auto'):
            # Load sales data
            sales_df = pd.read_csv(sales_path)

            # Load item items
            items_df = pd.read_csv(
                items_path,
                usecols=['item_id', 'item_category_id'],
                index_col=['item_id']
            )
            data = {'items': items_df}

            # Group item prices
            prices_df = sales_df[['shop_id', 'item_id', 'item_price']]
            prices_df = prices_df.groupby(
                by=['shop_id', 'item_id']
            ).agg('mean')
            data['prices'] = prices_df

            # Drop date and item_price from dataframe
            sales_df.drop(columns=['date', 'item_price'], inplace=True)

            # Group item count
            sales_df = sales_df.groupby(
                by=['shop_id', 'item_id', 'date_block_num']
            ).agg('sum')
            data['sales'] = sales_df

            # Get and store batches of data
            self.batches = self.batch_data(data)
        else:
            # Store batches and item prices
            self.batches = batches
        
        self.shuffle = shuffle
        self.seed = seed

        # Shuffle data
        if (shuffle):
            random.seed(seed)
            random.shuffle(self.batches)

    def __len__(self):
        """ Returns the number of batches. """
        return len(self.batches)
    
    def __getitem__(self, idx):
        """ Gets the idx'th batch of data. """
        return self.batches[idx]
    
    def batch_data(self, data):
        """ Batches data. """
        # Get unique shop and item id pairs
        ids = data['sales'].index.droplevel('date_block_num')
        ids = list(ids.unique())

        # Create batches
        batches = []
        num_batches = np.ceil(len(ids) / self.batch_size).astype('int32')
        prog_bar =tf.keras.utils.Progbar(num_batches)
        for idx in range(num_batches):
            low = idx * self.batch_size
            high = min((idx + 1)* self.batch_size, len(ids))
            num_samples = high - low

            # Create batch
            sales_batch = np.zeros((num_samples, self.seq_len, 12), dtype='float32')
            items_batch = np.empty(num_samples, dtype='int32')
            prices_batch = np.empty(num_samples, dtype='float32')
            y_batch = np.empty(num_samples)

            for i, (shop_id, item_id) in enumerate(ids[low:high]):
                # Create sales sequence
                sales = data['sales'].loc[shop_id, item_id,:]
                seq = np.zeros((self.seq_len+1,12))
                for date_block_num, item_cnt in sales.itertuples():
                    seq[date_block_num, date_block_num%12] += item_cnt
                
                # Add add sequence to sales_batch and y_batch
                sales_batch[i] = seq[:-1]
                y_batch[i] = np.sum(seq[-1])

                # Add category id to items_batch
                items_batch[i] = data['items'].loc[item_id]

                # Add price to price_batch
                prices_batch[i] = data['prices'].loc[(shop_id, item_id)]
            
                batches.append(((sales_batch, items_batch, prices_batch), y_batch))
            
            # Update progress bar
            prog_bar.update(idx)
        
        return batches

    def split_generator(self, frac=0.2, shuffle=True, seed=0):
        """
        Removes a fraction of the data from the data generator, and returns a
        new DataGenerator with the removed data and the same attributes. If 
        shuffle is set to False split_generator removes and adds the last data
        points from the data generator.
        """
        num_batches = len(self)
        num_samples = int(frac * len(self.batches))
        # Sample batches
        sample_batches = []
        if (shuffle):
            # Remove and add the ids randomly from the data generator
            random.seed(seed)
            for i in reversed(range(num_batches-num_samples, num_batches)):
                sample_batches.append(self.batches.pop(random.randrange(i)))
        else:
            # Remove and add the last ids from the data generator
            for i in range(num_samples):
                sample_batches.append(self.batches.pop())

        return DataGenerator(
            batches=sample_batches,
            batch_size=self.batch_size,
            seq_len=self.seq_len,
            shuffle=self.shuffle,
            seed=self.seed
        )