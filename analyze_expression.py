import scanpy as sc
import pandas as pd

# Load adipose tissue scRNA-seq data
adata_adipose = sc.read_h5ad("./data/biomni_data/data_lake/scRNA_seq_adipose_human_2023.h5ad")
adata_brain = sc.read_h5ad("./data/biomni_data/data_lake/scRNA_seq_brain_human_2023.h5ad")

# Extract ZNF797 expression
if 'ZNF797' in adata_adipose.var_names:
    adipose_expr = adata_adipose[:, 'ZNF797'].X.toarray().flatten()
    # Get cell type annotations
    cell_types_adipose = adata_adipose.obs['cell_type'].values
    # Filter for mature adipocytes
    mature_adipocytes = (cell_types_adipose == 'mature adipocyte')
    mean_expr_adipocyte = adipose_expr[mature_adipocytes].mean()
else:
    mean_expr_adipocyte = None

if 'ZNF797' in adata_brain.var_names:
    brain_expr = adata_brain[:, 'ZNF797'].X.toarray().flatten()
    cell_types_brain = adata_brain.obs['cell_type'].values
    # Filter for neurons
    neurons = (cell_types_brain == 'neuron')
    mean_expr_neuron = brain_expr[neurons].mean()
else:
    mean_expr_neuron = None

# Output results
print(f"Mean ZNF797 expression in mature adipocytes: {mean_expr_adipocyte}")
print(f"Mean ZNF797 expression in neurons: {mean_expr_neuron}")
