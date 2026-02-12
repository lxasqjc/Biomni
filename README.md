# CLUSTER RNAseq deconvolution project 2023

Five datasets are uploaded and listed in the table below.

	    fileName                             Description
	-----------------------------------------------------------------------------
	1 | Sample_annotated_Zenodo.csv        | Sample annotation
	2 | RawReadCounts_Zenodo.csv           | Raw read count matrix
	3 | BatchCorrectedReadCounts_Zenodo.csv| Batch-corrected read count matrix
	4 | GeneMetaInfo_Zenodo.csv            | Gene Information
	5 | FlowSorterFraction_Zenodo.csv      | Cell type fractions

## Description of the data and file structure

**Sample_annotated_Zenodo.csv**

------------------------------------------------------------------------

There are 723 rows (samples) and 6 columns in this file. Definitions of
column variables are explained in the following.

- **sample**: sample names used in read count matrices

- **samp**: subject Id

- **samtype**: refsamp for training samples; nonrefsamp for testing
  samples

- **cell type**: PBMC, CD4, CD8, CD14, CD19

- **batch**: RNAseq sequencing batch

- **sex**: M for male; F for female

The first 3 rows of this dataset are shown below.

           sample   samp samtype celltype batch sex
    1:  CHC096CD4 CHC096 refsamp      CD4     1   M
    2:  CHC096CD8 CHC096 refsamp      CD8     1   M
    3: CHC096CD14 CHC096 refsamp     CD14     1   M

**RawReadCounts_Zenodo.csv**

------------------------------------------------------------------------

Raw read count matrix (59453 genes \* 723 samples). **Gene’s name is the
first column without a header (column name)**. featureCount was used to summarise read
counts based on Homo_sapiens.GRCh38.103.gtf.

Read counts of the first 5 genes for the first 6 samples are shown
below.

                CHC096CD4 CHC096CD8 CHC096CD14 CHC096CD19 CHC096PBMC THC040CD4
    DDX11L1           247       255        128        167        214        38
    WASH7P          10377      8277       6570       7641       6263      2890
    MIR6859-1         229       199         94         84         70        34
    MIR1302-2HG         3         0          3          1          0         0
    MIR1302-2           0         0          0          0          0         0

**BatchCorrectedReadCounts_Zenodo.csv**

------------------------------------------------------------------------

Batch-corrected read count matrix (59453 genes \* 723 samples) derived
using
[Combat-Seq](https://academic.oup.com/nargab/article/2/3/lqaa078/5909519).
**Gene’s name is the first column without a header (column name).**

Batch-corrected read counts of the first 5 genes for the first 6 samples
are shown below.

                CHC096CD4 CHC096CD8 CHC096CD14 CHC096CD19 CHC096PBMC THC040CD4
    DDX11L1           175       182         90        117        152        27
    WASH7P           6463      5144       4251       4916       4022      1882
    MIR6859-1         143       123         68         62         52        26
    MIR1302-2HG         3         0          4          1          0         0
    MIR1302-2           0         0          0          0          0         0

**GeneMetaInfo_Zenodo.csv**

------------------------------------------------------------------------

Information on gene name (**Geneid**), chromosome (**Chr**), gene length
(**Length**), gene type (**gene_biotype**) for 59453 genes (rows).
**Gene’s name is the first column without a header (column name).**

The first 3 rows of this dataset are shown below.

                 Geneid Chr Length                       gene_biotype
    DDX11L1     DDX11L1   1   1735 transcribed_unprocessed_pseudogene
    WASH7P       WASH7P   1   1351             unprocessed_pseudogene
    MIR6859-1 MIR6859-1   1     68                              miRNA

**FlowSorterFraction_Zenodo.csv**

------------------------------------------------------------------------

Organised by PBMC sample names of subjects (rows) and cell types
(columns). Cell type fractions were derived from flow sorter data. For each subject, we divided CD4, CD8, CD14, and CD19 cell counts by the sum of CD4, CD8, CD14 and CD19 cells to obtain cell-type fractions.


The first 3 rows of this dataset are shown below.

                     CD4       CD8      CD14      CD19
    CHC096PBMC 0.4269334 0.2493598 0.1552741 0.1684327
    THC040PBMC 0.4951259 0.2367423 0.1413210 0.1268107
    CHC177PBMC 0.4745677 0.2221926 0.1956962 0.1075434

## Code/Software

- Raw read counts were generated using
  [RSSnextflow](https://gitlab.com/b8307038/rssnextflow), customised
  pipeline for UMI-tagged RNAseq data.

- These datasets were utilised in the [imputation of cell-type
  expression workflow](https://gitlab.com/b8307038/deconvimpvexpr) for
  this preprint-[Imputation of cell-type specific expression using
  RNA-seq data from mixed cell
  populations](https://doi.org/10.1101/2023.09.11.556650).
