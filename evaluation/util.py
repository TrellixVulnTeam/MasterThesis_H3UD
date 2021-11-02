import torch
import numpy as np

def split_labels_into_id_and_ood(y, id_labels, ood_labels=None, id_label=0, ood_label=1):
    """ Creates new labels that correspond to in-distribution and out-ouf-distribution.
    
    Paramters:
    ----------
    y : torch.tensor, shape [N]
        Original class labels.
    id_labels : iterable
        All in-distribution labels.
    ood_labels : iterable
        All out-of-distribution labels or None. If None, it will be set to all labels in y that are not id.
    id_label : int
        The new label of id points.
    ood_label : int
        The new label of ood points.

    Returns:
    --------
    y_new : torch.tensor, shape [N]
        Labels corresponding to id and ood data.
    """
    if ood_labels is None:
        ood_labels = set(torch.unique(y).tolist()) - set(id_labels)

    y_new = torch.zeros_like(y)
    for label in id_labels:
        y_new[y == label] = id_label
    for label in ood_labels:
        y_new[y == label] = ood_label
    return y_new

def get_data_loader(name, loaders):
    """ Gets the right dataloader given the name of a dataset. """
    name = name.lower()
    if name == 'train':
        return loaders['data_loader_train']
    elif name in ('val-reduced', 'val_reduced'):
        return loaders['data_loader_val']
    elif name in ('val'):
        return loaders['data_loader_val_all_classes']
    else:
        raise RuntimeError(f'Cant provide dataset {name} to evaluation.')

def feature_extraction(model, data_loaders, gpus=0, layer=-2):
    """ Extracts features of all data loaders. 
    
    model : torch.nn.Module
        A model to use as a feature extractor
    data_loaders : list
        A list of data loaders to extract features for.
    gpus : int
        If > 0, models are run on the gpu.
    layer : int
        Which layer to use for feature extraction.

    Returns:
    --------
    features : list
        A list of features for each dataset.
    labels : list
        A list of correpsonding labels for each dataset.
    """
    if gpus > 0:
        model = model.to('cuda')
    
    features, labels = [], []
    for loader in data_loaders:
        assert len(loader) == 1, f'Feature extraction is currently only supported for single graphs.'
        for data in loader:
            if gpus > 0:
                data = data.to('cuda')
            features.append(model(data)[layer][data.mask].cpu())
            labels.append(data.y[data.mask].cpu())
    return features, labels
