import warnings

import torch
import numpy as np
import os.path as osp
import os
import json


from model.gnn import make_model_by_configuration
from model.semi_supervised_node_classification import SemiSupervisedNodeClassification
from data.gust_dataset import GustDataset
from data.util import data_get_num_attributes, data_get_num_classes
from seed import model_seeds
from torch_geometric.loader import DataLoader
import torch.nn.functional as F
import pytorch_lightning as pl
from pytorch_lightning.callbacks.early_stopping import EarlyStopping
from util import suppress_stdout
from pytorch_lightning.loggers import WandbLogger, TensorBoardLogger
import contextlib, os
from pytorch_lightning.callbacks.model_checkpoint import ModelCheckpoint
from training_semi_supervised_node_classification import ExperimentWrapper
import data.constants as dconstants

# ex.init_dataset(dataset='cora_ml', num_dataset_splits=1, train_portion=0.05, val_portion=0.15, test_portion=0.6, test_portion_fixed=0.2,
#                     train_labels=[0, 1, 2, 3, 4, 5], val_labels='all', train_labels_remove_other=False, val_labels_remove_other=False,
#                     split_type='stratified',
#                     )

num_splits, num_inits = 2, 1


ex = ExperimentWrapper(init_all=False, collection_name='model-test', run_id='gcn_64_32_residual')
# ex.init_dataset(dataset='cora_ml', num_dataset_splits=num_splits, train_portion=20, val_portion=20, test_portion=0.6, test_portion_fixed=0.2,
#                     train_labels_remove_other=True, val_labels_remove_other=True,
#                     split_type='uniform',
#                     train_labels = [
#                         'Artificial_Intelligence/Machine_Learning/Case-Based', 
#                         'Artificial_Intelligence/Machine_Learning/Theory', 
#                         # 'Artificial_Intelligence/Machine_Learning/Genetic_Algorithms', 
#                         'Artificial_Intelligence/Machine_Learning/Probabilistic_Methods', 
#                         'Artificial_Intelligence/Machine_Learning/Neural_Networks',
#                         'Artificial_Intelligence/Machine_Learning/Rule_Learning',
#                         # 'Artificial_Intelligence/Machine_Learning/Reinforcement_Learning',
#                     ], 
#                     # val_labels = 'all',
#                     val_labels = [
#                         'Artificial_Intelligence/Machine_Learning/Case-Based', 
#                         'Artificial_Intelligence/Machine_Learning/Theory', 
#                         # 'Artificial_Intelligence/Machine_Learning/Genetic_Algorithms', 
#                         #'Artificial_Intelligence/Machine_Learning/Probabilistic_Methods', 
#                         #'Artificial_Intelligence/Machine_Learning/Neural_Networks',
#                         #'Artificial_Intelligence/Machine_Learning/Rule_Learning',
#                         'Artificial_Intelligence/Machine_Learning/Reinforcement_Learning',
#                     ], 
#                     base_labels = 'all',
# )
ex.init_dataset(dataset='cora_full', num_dataset_splits=num_splits, train_portion=20, test_portion_fixed=0.2,
                    split_type='uniform',
                    type='npz',
                    #base_labels='all',
                    #train_labels=['class_0', 'class_1'],
                    #val_labels='all',
                    base_labels = ['Artificial_Intelligence/NLP', 'Artificial_Intelligence/Data_Mining','Artificial_Intelligence/Speech', 'Artificial_Intelligence/Knowledge_Representation','Artificial_Intelligence/Theorem_Proving', 'Artificial_Intelligence/Games_and_Search','Artificial_Intelligence/Vision_and_Pattern_Recognition', 'Artificial_Intelligence/Planning','Artificial_Intelligence/Agents','Artificial_Intelligence/Robotics', 'Artificial_Intelligence/Expert_Systems','Artificial_Intelligence/Machine_Learning/Case-Based', 'Artificial_Intelligence/Machine_Learning/Theory', 'Artificial_Intelligence/Machine_Learning/Genetic_Algorithms', 'Artificial_Intelligence/Machine_Learning/Probabilistic_Methods', 'Artificial_Intelligence/Machine_Learning/Neural_Networks','Artificial_Intelligence/Machine_Learning/Rule_Learning','Artificial_Intelligence/Machine_Learning/Reinforcement_Learning','Operating_Systems/Distributed', 'Operating_Systems/Memory_Management', 'Operating_Systems/Realtime', 'Operating_Systems/Fault_Tolerance'],
                    train_labels = ['Artificial_Intelligence/Machine_Learning/Case-Based', 'Artificial_Intelligence/Machine_Learning/Theory', 'Artificial_Intelligence/Machine_Learning/Genetic_Algorithms', 'Artificial_Intelligence/Machine_Learning/Probabilistic_Methods', 'Artificial_Intelligence/Machine_Learning/Neural_Networks','Artificial_Intelligence/Machine_Learning/Rule_Learning','Artificial_Intelligence/Machine_Learning/Reinforcement_Learning'],
                    left_out_class_labels = ['Operating_Systems/Distributed', 'Operating_Systems/Memory_Management', 'Operating_Systems/Realtime', 'Operating_Systems/Fault_Tolerance'],
                    corpus_labels = ['Artificial_Intelligence/Machine_Learning/Case-Based', 'Artificial_Intelligence/Machine_Learning/Theory', 'Artificial_Intelligence/Machine_Learning/Genetic_Algorithms', 'Artificial_Intelligence/Machine_Learning/Probabilistic_Methods', 'Artificial_Intelligence/Machine_Learning/Neural_Networks','Artificial_Intelligence/Machine_Learning/Rule_Learning','Artificial_Intelligence/Machine_Learning/Reinforcement_Learning'],
                    preprocessing='bag-of-words',
                    #ood_type = dconstants.LEFT_OUT_CLASSES[0],
                    ood_type = dconstants.PERTURBATION[0],
                    setting = dconstants.TRANSDUCTIVE[0],
                    #preprocessing='word_embedding',
                    #language_model = 'bert-base-uncased',
                    #language_model = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
                    #language_model = 'allenai/longformer-base-4096',
                    drop_train_vertices_portion = 0.1,
                    )

ex.init_model(model_type='gcn', hidden_sizes=[64], num_initializations=num_inits, weight_scale=2.0, 
    use_spectral_norm=False, use_bias=True, activation='leaky_relu', leaky_relu_slope=0.01,
    residual=True, freeze_residual_projection=False, num_ensemble_members=1, num_samples=1,
    use_spectral_norm_on_last_layer=False, self_loop_fill_value=1.0,
    #dropout=0.5, drop_edge=0.5,
    )
ex.init_run(name='model_{0}_hidden_sizes_{1}_weight_scale_{2}_setting_{3}_ood_type_{4}', args=[
    'model:model_type', 'model:hidden_sizes', 'model:weight_scale', 'data:setting', 'data:ood_type',
])

# pipeline = []

# pipeline += [{
#         'type' : 'EvaluateEmpircalLowerLipschitzBounds',
#         'num_perturbations' : 20,
#         'min_perturbation' : 2,
#         'max_perturbation' : 10,
#         'num_perturbations_per_sample' : 5,
#         'perturbation_type' : 'noise',
#         'seed' : 1337,
#         'name' : 'noise_perturbations',
#     },]

# # Perturbed datasets
# pipeline += [{
#         'type' : 'PerturbData',
#         'base_data' : 'val-reduced',
#         'dataset_name' : 'val-reduced-ber',
#         'perturbation_type' : 'bernoulli',
#         'budget' : 0.1,
#         'parameters' : {
#             'p' : 0.5,
#         },
#         'perturb_in_mask_only' : True,
#     },
#     {
#         'type' : 'PerturbData',
#         'base_data' : 'val-reduced',
#         'dataset_name' : 'val-reduced-normal',
#         'perturbation_type' : 'normal',
#         'budget' : 0.1,
#         'parameters' : {
#             'scale' : 1.0,
#         },
#         'perturb_in_mask_only' : True,
#     },]

# for dataset, short in (('val-reduced-ber', 'ber'), ('val-reduced-normal', 'normal'), ('val', 'loc')):
#     for remove_edges in (True, False):
        
#         if remove_edges:
#             name = short + '-no-edges'
#         else:
#             name = short

#         if short == 'loc':
#             ood_cfg = {
#                 'separate_distributions_by' : 'neighbourhood',
#                 'separate_distributions_tolerance' : 0.1,
#                 'kind' : 'leave_out_classes', 
#             }
#         else:
#             ood_cfg = {
#                 'kind' : 'perturbations',
#             }

#         if dataset == 'val':
#             dataset_acc = 'val-reduced'
#         else:
#             dataset_acc = dataset

#         # pipeline.append({
#         #     'type' : 'EvaluateAccuracy',
#         #     'evaluate_on' : [dataset_acc],
#         #     'model_kwargs' : {'remove_edges' : remove_edges},
#         #     'name' : name,
#         # } | ood_cfg)
#         # pipeline.append({
#         #     'type' : 'EvaluateCalibration',
#         #     'evaluate_on' : [dataset_acc],
#         #     'name' : name,
#         # })
#         # pipeline.append({
#         #     'type' : 'EvaluateSoftmaxEntropy',
#         #     'evaluate_on' : [dataset],
#         #     'model_kwargs' : {'remove_edges' : remove_edges},
#         #     'name' : name,
#         # } | ood_cfg)
#         # pipeline.append({
#         #     'type' : 'EvaluateLogitEnergy',
#         #     'evaluate_on' : [dataset],
#         #     'model_kwargs' : {'remove_edges' : remove_edges},
#         #     'name' : name,
#         # } | ood_cfg)
#         pipeline.append({
#             'type' : 'FitFeatureDensityGrid',
#             'fit_to' : ['train'],
#             'fit_to_ground_truth_labels' : ['train'],
#             'evaluate_on' : [dataset],
#             'density_types' : {
#                 'GaussianPerClass' : {
#                     'diagonal_covariance' : [True],
#                     'relative' : [True, False],
#                     'mode' : ['weighted', 'max'],
#                 },
#                 'FeatureSpaceDensityNormalizingFlowPerClass' : {
#                     # 'iterations' : [10],
#                     # 'relative' : [True, False],
#                     # 'mode' : ['weighted', 'max'],
#                     # 'num_layers' : [10],
#                     'iterations' : [10],
#                     'relative' : [True],
#                     'mode' : ['weighted'],
#                     'num_layers' : [2],
#                     'hidden_dim' : [64],
#                     'flow_type' : ['maf'],

#                 },
#             },
#             'dimensionality_reductions' : {
#                 'none' : {
#                 }
#             },
#             'log_plots' : True,
#             'model_kwargs_evaluate' : {'remove_edges' : remove_edges},
#             'name' : name,
#         } | ood_cfg)
        

ex.init_evaluation(
    save_artifacts=False,
    print_pipeline=True,
    pipeline= 
    [
    {
        'type' : 'PerturbData',
        'base_data' : 'ood',
        'dataset_name' : 'ood-ber',
        'perturbation_type' : 'bernoulli',
        'parameters' : {
            'p' : 0.5,
        },
    },
    {
        'type' : 'PerturbData',
        'base_data' : 'ood',
        'dataset_name' : 'ood-normal',
        'perturbation_type' : 'normal',
        'parameters' : {
            'scale' : 1.0,
        },
    },
    {
        'type' : 'VisualizeIDvsOOD',
        'fit_to' : ['train'],
        'evalaute_on' : ['ood'],
        'separate_distributions_by' : 'ood-and-neighbourhood',
        'separate_distributions_tolerance' : 0.1,
        'kind' : 'leave_out_classes',
        'dimensionality_reductions' : ['pca', 'tsne',],
    },
    {
        'type' : 'VisualizeIDvsOOD',
        'fit_to' : ['train'],
        'evalaute_on' : ['ood'],
        'separate_distributions_by' : 'ood-and-neighbourhood',
        'separate_distributions_tolerance' : 0.1,
        'kind' : 'leave_out_classes',
        'layer' : -1,
        'name' : 'logits',
        'dimensionality_reductions' : ['pca', 'tsne',],
    },
    {
        'type' : 'EvaluateEmpircalLowerLipschitzBounds',
        'num_perturbations' : 2,
        'num_perturbations_per_sample' : 2,
        'permute_per_sample' : True,
        'perturbation_type' : 'derangement',
        'seed' : 1337,
        'name' : 'derangement_perturbations',
    },
    {
        'type' : 'EvaluateEmpircalLowerLipschitzBounds',
        'num_perturbations' : 20,
        'min_perturbation' : 2,
        'max_perturbation' : 10,
        'num_perturbations_per_sample' : 5,
        'perturbation_type' : 'noise',
        'seed' : 1337,
        'name' : 'noise_perturbations',
    },
    {
        'type' : 'FitFeatureSpacePCA',
        'fit_to' : ['train', 'val'],
        'evaluate_on' : ['train', 'val', 'ood-normal'],
        'num_components' : 2,
        'name' : '2d-pca-normal',
    },
    {
        'type' : 'FitFeatureSpacePCA',
        'fit_to' : ['train', 'val'],
        'evaluate_on' : ['train', 'val', 'ood-ber'],
        'num_components' : 2,
        'name' : '2d-pca-ber',
    },
    {
        'type' : 'EvaluateAccuracy',
        'evaluate_on' : ['ood-normal'],
        'separate_distributions_by' : 'ood-and-neighbourhood',
        'separate_distributions_tolerance' : 0.1,
    },
    {
        'type' : 'EvaluateAccuracy',
        'evaluate_on' : ['ood-ber'],
        'separate_distributions_by' : 'ood-and-neighbourhood',
        'separate_distributions_tolerance' : 0.1,
    },
    {
        'type' : 'EvaluateCalibration',
        'evaluate_on' : ['val'],
    },
    {
        'type' : 'EvaluateSoftmaxEntropy',
        'evaluate_on' : ['ood-normal'],
        'separate_distributions_by' : 'ood-and-neighbourhood',
        'separate_distributions_tolerance' : 0.1,
        'name' : 'normal',
    },
    {
        'type' : 'EvaluateSoftmaxEntropy',
        'evaluate_on' : ['ood-ber'],
        'separate_distributions_by' : 'ood-and-neighbourhood',
        'separate_distributions_tolerance' : 0.1,
        'name' : 'ber',
    },
    {
        'type' : 'FitFeatureDensityGrid',
        'fit_to' : ['train'],
        'fit_to_ground_truth_labels' : ['train'],
        'evaluate_on' : ['ood-normal'],
        'name' : 'normal',
        'density_types' : {
            'GaussianPerClass' : {
                'diagonal_covariance' : [True],
                'relative' : [True, False],
                'mode' : ['weighted', 'max'],
            },
        },
        'dimensionality_reductions' : {
            'pca' : {
                'number_components' : [2],
            },
            'none' : {
            }
        },
        'separate_distributions_by' : 'ood-and-neighbourhood',
        'separate_distributions_tolerance' : 0.1,
        'kind' : 'leave_out_classes',
        'log_plots' : True,
    },
    {
        'type' : 'FitFeatureDensityGrid',
        'fit_to' : ['train'],
        'fit_to_ground_truth_labels' : ['train'],
        'evaluate_on' : ['ood-ber'],
        'name' : 'ber',
        'density_types' : {
            'GaussianPerClass' : {
                'diagonal_covariance' : [True],
                'relative' : [True, False],
                'mode' : ['weighted', 'max'],
            },
        },
        'dimensionality_reductions' : {
            'pca' : {
                'number_components' : [2],
            },
            'none' : {
            }
        },
        'separate_distributions_by' : 'ood-and-neighbourhood',
        'separate_distributions_tolerance' : 0.1,
        'kind' : 'leave_out_classes',
        'log_plots' : True,
    },
    # {
    #     'type' : 'EvaluateAccuracy',
    #     'evaluate_on' : ['val-reduced'],
    #     'model_kwargs' : {'remove_edges' : True},
    #     'name' : 'no-edges',
    # },
    # {
    #     'type' : 'EvaluateAccuracy',
    #     'evaluate_on' : ['val-reduced-ber'],
    # },
    # {
    #     'type' : 'EvaluateAccuracy',
    #     'evaluate_on' : ['val'],
    #     'separate_distributions_by' : 'neighbourhood',
    #     'separate_distributions_tolerance' : 0.1,
    #     'kind' : 'leave_out_classes',
    #     'name' : 'loc',
    # },
    # {
    #     'type' : 'PrintDatasetSummary',
    #     'evaluate_on' : ['train', 'val-reduced', 'val-reduced-ber'],
    # },
    # {
    #     'type' : 'EvaluateSoftmaxEntropy',
    #     'name' : 'loc-no-edges',
    #     'evaluate_on' : ['val'],
    #     'separate_distributions_by' : 'neighbourhood',
    #     'separate_distributions_tolerance' : 0.1,
    #     'kind' : 'leave_out_classes',
    #     'model_kwargs_evaluate' : {'remove_edges' : True},
    # },
    # {
    #     'type' : 'EvaluateSoftmaxEntropy',
    #     'evaluate_on' : ['val-reduced-normal'],
    #     'kind' : 'perturbations',
    #     'name' : 'normal'
    # },
    # {
    #     'type' : 'EvaluateSoftmaxEntropy',
    #     'name' : 'normal-no-edges',
    #     'evaluate_on' : ['val-reduced-normal'],
    #     'kind' : 'perturbations',
    #     'model_kwargs_evaluate' : {'remove_edges' : True},
    # },
    # {
    #     'type' : 'EvaluateLogitEnergy',
    #     'evaluate_on' : ['val'],
    #     'separate_distributions_by' : 'neighbourhood',
    #     'separate_distributions_tolerance' : 0.1,
    #     'kind' : 'leave_out_classes',
    # },
    # {
    #     'type' : 'EvaluateLogitEnergy',
    #     'name' : 'no-edges',
    #     'evaluate_on' : ['val'],
    #     'separate_distributions_by' : 'neighbourhood',
    #     'separate_distributions_tolerance' : 0.1,
    #     'kind' : 'leave_out_classes',
    #     'model_kwargs_evaluate' : {'remove_edges' : True},
    # },
    # {
    #     'type' : 'LogInductiveFeatureShift',
    #     'data_before' : 'train',
    #     'data_after' : 'val',
    # },
    # {
    #     'type' : 'LogInductiveSoftmaxEntropyShift',
    #     'data_before' : 'train',
    #     'data_after' : 'val',
    # },
    # {
    #     'type' : 'FitFeatureDensityGrid',
    #     'fit_to' : ['train'],
    #     'fit_to_ground_truth_labels' : ['train'],
    #     'evaluate_on' : ['val'],
    #     'density_types' : {
    #         'GaussianPerClass' : {
    #             'diagonal_covariance' : [True],
    #             'relative' : [True, False],
    #             'mode' : ['weighted', 'max'],
    #         },
    #     },
    #     'dimensionality_reductions' : {
    #         'none' : {
    #         }
    #     },
    #     'separate_distributions_by' : 'neighbourhood',
    #     'separate_distributions_tolerance' : 0.1,
    #     'kind' : 'leave_out_classes',
    #     'log_plots' : True,
    #     'name' : 'loc',
    # },
    # {
    #     'type' : 'FitFeatureDensityGrid',
    #     'fit_to' : ['train'],
    #     'fit_to_ground_truth_labels' : ['train'],
    #     'evaluate_on' : ['val'],
    #     'density_types' : {
    #         'GaussianPerClass' : {
    #             'diagonal_covariance' : [True],
    #             'relative' : [True, False],
    #             'mode' : ['weighted', 'max'],
    #         },
    #     },
    #     'dimensionality_reductions' : {
    #         'none' : {
    #         }
    #     },
    #     'separate_distributions_by' : 'neighbourhood',
    #     'separate_distributions_tolerance' : 0.1,
    #     'kind' : 'leave_out_classes',
    #     'log_plots' : True,
    #     'model_kwargs_evaluate' : {'remove_edges' : True},
    #     'name' : 'loc-no-edges',
    # },
    # {
    #     'type' : 'FitFeatureDensityGrid',
    #     'fit_to' : ['train'],
    #     'fit_to_ground_truth_labels' : ['train'],
    #     'evaluate_on' : ['val-reduced-normal'],
    #     'density_types' : {
    #         'GaussianPerClass' : {
    #             'diagonal_covariance' : [True],
    #             'relative' : [True, False],
    #             'mode' : ['weighted', 'max'],
    #         },
    #     },
    #     'dimensionality_reductions' : {
    #         'none' : {
    #         }
    #     },
    #     'kind' : 'perturbations',
    #     'log_plots' : True,
    #     'name' : 'normal',
    # },
    # {
    #     'type' : 'FitFeatureDensityGrid',
    #     'fit_to' : ['train'],
    #     'fit_to_ground_truth_labels' : ['train'],
    #     'evaluate_on' : ['val-reduced-normal'],
    #     'density_types' : {
    #         'GaussianPerClass' : {
    #             'diagonal_covariance' : [True],
    #             'relative' : [True, False],
    #             'mode' : ['weighted', 'max'],
    #         },
    #     },
    #     'dimensionality_reductions' : {
    #         'none' : {
    #         }
    #     },
    #     'kind' : 'perturbations',
    #     'log_plots' : True,
    #     'model_kwargs_evaluate' : {'remove_edges' : True},
    #     'name' : 'normal-no-edges',
    # },
    # {
    #     'type' : 'FitFeatureDensityGrid',
    #     'name' : 'no-edges',
    #     'fit_to' : ['train'],
    #     'fit_to_ground_truth_labels' : ['train'],
    #     'evaluate_on' : ['val'],
    #     'density_types' : {
    #         'GaussianPerClass' : {
    #             'diagonal_covariance' : [True],
    #             'relative' : [True, False],
    #             'mode' : ['weighted', 'max'],
    #         },
    #     },
    #     'dimensionality_reductions' : {
    #         'none' : {
    #         }
    #     },
    #     'separate_distributions_by' : 'neighbourhood',
    #     'separate_distributions_tolerance' : 0.1,
    #     'kind' : 'leave_out_classes',
    #     'log_plots' : True,
    #     'model_kwargs_evaluate' : {'remove_edges' : True},
    # },
    ],
    ignore_exceptions=False,
)

results_path = (ex.train(max_epochs=1000, learning_rate=0.001, early_stopping={
    'monitor' : 'val_loss',
    'mode' : 'min',
    'patience' : 50,
    'min_delta' : 1e-3,
}, gpus=0, suppress_stdout=False))

with open(results_path) as f:
    print(json.load(f))