import random
import numpy as np
import tensorflow as tf

from database import SalesDB

class DataGenerator(tf.keras.utils.PyDataset):

    """
    DataGenerator generates and preprocesses batches of data from a database.
    The connections, and queries are made using the SalesDB interface. 
    """
    
    def __init__(
            self,
            user=None,
            password=None,
            ids='auto',
            sales_db=None,
            batch_size=32,
            seq_len=34,
            shuffle=True,
            seed=0,
            **krwags
        ):
        """
        Args:
            user: The user's name needed to connect with the database.
            password: The user's password needed to connect with the database.
            ids: If ids is set to auto, the list of shop, item id pairs are
                retrieved from the database. Otherwise, ids is a list of shop,
                item id pairs.
            batch_size: The size of each batch of data. If the number of
                ids is not a multiple of the batch size, the last batch is 
                smaller.
            seq_len: The length of each sequence of monthly sales data.
            shuffle: If True, shuffles the data with seed value.
            seed: Seed value used to shuffle data.
        """
        super().__init__(**krwags)

        # Create SalesDb
        if not(sales_db):
            self.sales_db = SalesDB(user, password)
        else:
            self.sales_db = sales_db
        
        # Get shop, item id pairs
        if (ids == 'auto'):
            self.ids = self.sales_db.getIds()
        else:
            self.ids = ids

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
            'sequences': np.zeros((num_samples,self.seq_len,12), dtype='float32')
        }
        y_batch = np.empty(num_samples)

        # Get data from database
        for i, (shop_id,item_id) in enumerate(self.ids[low:high]):
            # Get item category id and price
            x_batch['categories'][i] = np.squeeze(self.sales_db.getItemCategory(shop_id,item_id))
            x_batch['prices'][i] = np.squeeze(self.sales_db.getItemPrice(shop_id,item_id))
            
            # Get sales data
            sales = self.sales_db.getSalesData(shop_id,item_id)
            for date_block_num, item_cnt in sales[:-1]:
                x_batch['sequences'][i,date_block_num,date_block_num%12] = item_cnt
            _, y_batch[i] = sales[-1]
        
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
    
    def summary(self):
        """ Prints a summary of all of the data in the data generator. """
        summary = f'number of data points {len(self.ids)}'
        print(summary)