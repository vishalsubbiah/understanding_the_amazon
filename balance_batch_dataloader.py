import random

from torch import np
from torch.utils.data.dataloader import DataLoader, DataLoaderIter
from torch.utils.data.sampler import RandomSampler


def generate_label_index_dict(dataset, logical_inds=None):
    """
    generate a dict mapping class names to image indices containing that label
    logical inds is a set of ones and zeros of the length of your data set
    used for train-val split
    """
    mlb_matrix = np.array(dataset.y_train)
    if logical_inds is None:
        logical_inds = np.ones(mlb_matrix.shape[0])
    test_matrix = np.eye(17)
    labels = dataset.mlb.inverse_transform(test_matrix)
    labels = [label[0] for label in labels]
    returndict = {}
    for label in labels:
        returndict[label] = np.array([])

    for col_index, label in enumerate(labels):
        col = mlb_matrix[:, col_index]
        ## elementwise multiplication of two arrays of ones and zeros
        filtr = (col > 0) * logical_inds
        returndict[label] = np.where(filtr)[0]

    return returndict

class BalanceSampler(RandomSampler):
    """
    sampler class to hold class_dict generated by generate_label_index_dict
    logical inds is a set of ones and zeros of the length of your data set
    used for train-val split
    """
    def __init__(self, dataset, logical_inds=None):
        if logical_inds is None:
            self.num_samples = len(dataset)
        else:
            self.num_samples = int(np.sum(logical_inds))
        self.class_dict = generate_label_index_dict(dataset, logical_inds)
        self.class_dict_keys = []
        ## this is to allow testing on a subset of data, normally the list
        ## of keys should just be all the keys
        for k, v in self.class_dict.items():
            if len(v) > 0:
                self.class_dict_keys.append(k)


class BalanceDataLoaderIter(DataLoaderIter):
    """
    data loader iterator that iterates over classes with equal probability
    """
    def _next_indices(self):
        batch_size = min(self.samples_remaining, self.batch_size)
        # batch = [next(self.sample_iter) for _ in range(batch_size)]
        batch = []
        ## list of keys in sampler
        keys = self.sampler.class_dict_keys
        for i in range(batch_size):
            randclass = random.choice(keys)
            idx = random.choice(self.sampler.class_dict[randclass])
            batch.append(idx)

        self.samples_remaining -= len(batch)
        return batch

class BalanceDataLoader(DataLoader):
    """
    dataloader that uses a BalanceDataLoaderIter and a BalanceSampler
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if kwargs['sampler'] is None:
            self.sampler = BalanceSampler(self.dataset)

    def __iter__(self):
        return BalanceDataLoaderIter(self)