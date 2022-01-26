import torch
import torch_geometric as tg
import matplotlib.pyplot as plt
import pytorch_lightning as pl
import numpy as np
import scipy.sparse as sp

from .base import *
import data.constants as dconstants
from .ood import OODDetection
from evaluation.util import run_model_on_datasets, get_data_loader
from evaluation.logging import *
from evaluation.callbacks import make_callback_get_data, make_callback_get_ground_truth, make_callback_get_mask
from data.util import vertex_intersection

@register_pipeline_member
class EvaluateStructure(OODDetection):

    name = 'EvaluateStructure'

    def __init__(self, fit_to=[dconstants.TRAIN], diffusion_iterations=16, teleportation_probability=0.2, gpus = 0, **kwargs):
        super().__init__(**kwargs)
        self.fit_to = fit_to
        self.diffusion_iterations = diffusion_iterations
        self.teleportation_probability = teleportation_probability
        self.gpus = gpus
    
    @property
    def configuration(self):
        return super().configuration | {
            'Fit to' : self.fit_to,
            'Diffusion iterations' : self.diffusion_iterations,
            'Teleportation Probability' : self.teleportation_probability,
        }

    def __call__(self, *args, **kwargs):
        data_fit = run_model_on_datasets(
            kwargs['model'], 
            [get_data_loader(name, kwargs['data_loaders']) for name in self.fit_to], 
            gpus=self.gpus, model_kwargs=self.model_kwargs_fit,
            callbacks=[
                make_callback_get_data()
            ]
        )[0]
        assert len(data_fit) == 1, f'Can only fit to one dataset'
        data_fit = data_fit[0]

        data_eval, labels_eval = run_model_on_datasets(
            kwargs['model'], 
            [get_data_loader(name, kwargs['data_loaders']) for name in self.evaluate_on], 
            gpus=self.gpus, model_kwargs=self.model_kwargs_fit,
            callbacks=[
                make_callback_get_data(),
                make_callback_get_ground_truth(),
            ]
        )
        assert len(data_eval) == 1, f'Can only eval on one dataset'
        data_eval = data_eval[0]
        labels_eval = torch.cat(labels_eval, 0)
        
        # Find the vertices in the `data_fit` mask on the `data_eval` dataset
        idx_intersection_fit, idx_intersection_eval = vertex_intersection(data_fit, data_eval)
        is_fit_intersection_eval = np.zeros(data_eval.x.size(0), dtype=bool)
        is_fit_intersection_eval[idx_intersection_eval] = data_fit.mask.numpy()[idx_intersection_fit]

        N = data_eval.x.size(0)
        A = sp.coo_matrix((np.ones(data_eval.edge_index.size(1)), data_eval.edge_index.numpy()), shape=(N, N)).tocsr()
        # Normalize adjacency
        # A += sp.coo_matrix(np.eye(A.shape[0]))
        degrees = A.sum(axis=0)[0].tolist()
        D = sp.diags(degrees, [0])
        D = D.power(-0.5)
        A = D.dot(A).dot(D)

        ppr = np.ones((N, N)) / N
        for _ in range(self.diffusion_iterations):
            ppr = (self.teleportation_probability * np.eye(N)) + ((1 - self.teleportation_probability) * (A @ ppr))
        ppr = torch.Tensor(ppr)
        diffused = torch.matmul(ppr, torch.Tensor(is_fit_intersection_eval.reshape(-1, 1)).float()).squeeze()



        # appnp = tg.nn.APPNP(self.diffusion_iterations, self.teleportation_probability, cached=False)
        # with torch.no_grad():
        #     # Diffuse the mask in `data_fit`
        #     diffused = appnp(torch.Tensor(is_fit_intersection_eval.reshape(-1, 1)).float(), data_eval.edge_index).squeeze()
        
        diffused = diffused[data_eval.mask]

        auroc_labels, auroc_mask, distribution_labels, distribution_label_names = self.get_distribution_labels(**kwargs)
        self.ood_detection(diffused, labels_eval,
                                'structure',
                                auroc_labels, auroc_mask, distribution_labels,
                                distribution_label_names, plot_proxy_log_scale=False, **kwargs
        )

        return args, kwargs
