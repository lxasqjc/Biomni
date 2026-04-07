# Data Lake Index

This index describes all files in the Biomni data lake.

**Most files are Parquet format — use `pd.read_parquet(path)` for fast columnar access.**

## Parquet Files

| File | Format | Size | Rows | Columns | Key Columns (first ~8) | Description |
|------|--------|------|------|---------|------------------------|-------------|
| `BindingDB_All_202409.parquet` | Parquet | 88.2 MB | 421,227 | 194 | BindingDB Reactant_set_id, Ligand SMILES, Ligand InChI, Ligand InChI Key, BindingDB MonomerID, BindingDB Ligand Name, Target Name, Target Source Organism According to Curator or DataSource | BindingDB binding assay data (Sept 2024) |
| `DepMap_CRISPRGeneDependency.parquet` | Parquet | 205.8 MB | 1,183 | 17917 | Unnamed: 0, A1BG (1), A1CF (29974), A2M (2), A2ML1 (144568), A3GALT2 (127550), A4GALT (53947), A4GNT (51146) | DepMap CRISPR gene dependency probabilities |
| `DepMap_CRISPRGeneEffect.parquet` | Parquet | 208.2 MB | 1,183 | 17917 | Unnamed: 0, A1BG (1), A1CF (29974), A2M (2), A2ML1 (144568), A3GALT2 (127550), A4GALT (53947), A4GNT (51146) | DepMap CRISPR gene effect scores |
| `DepMap_Model.parquet` | Parquet | 209.2 KB | 2,116 | 49 | ModelID, PatientID, CellLineName, StrippedCellLineName, DepmapModelType, OncotreeLineage, OncotreePrimaryDisease, OncotreeSubtype | DepMap cell line model metadata |
| `DepMap_OmicsExpressionProteinCodingGenesTPMLogp1.parquet` | Parquet | 266.1 MB | 1,684 | 19206 | Unnamed: 0, TSPAN6 (7105), TNMD (64102), DPM1 (8813), SCYL3 (57147), FIRRM (55732), FGR (2268), CFH (3075) | DepMap gene expression TPM log(p+1) |
| `DisGeNET.parquet` | Parquet | 3.0 MB | 9,828 | 2 | Disorder, Genes | DisGeNET gene-disease associations |
| `McPAS-TCR.parquet` | Parquet | 1.0 MB | 40,731 | 29 | CDR3.alpha.aa, CDR3.beta.aa, Species, Category, Pathology, Pathology.Mesh.ID, Additional.study.details, Antigen.identification.method | McPAS-TCR antigen-specific TCR database |
| `Virus-Host_PPI_P-HIPSTER_2020.parquet` | Parquet | 793.1 KB | 6,715 | 2 | Viral Protien, Genes | P-HIPSTer 2020 virus-host protein interactions |
| `affinity_capture-ms.parquet` | Parquet | 5.6 MB | 347,271 | 9 | interaction_id, gene_a_id, gene_b_id, experimental_system_type, pubmed_id, organism_id_a, organism_id_b, throughput_type | BioGRID affinity capture MS interactions |
| `affinity_capture-rna.parquet` | Parquet | 43.0 KB | 2,235 | 9 | interaction_id, gene_a_id, gene_b_id, experimental_system_type, pubmed_id, organism_id_a, organism_id_b, throughput_type | BioGRID affinity capture RNA interactions |
| `broad_repurposing_hub_molecule_with_smiles.parquet` | Parquet | 1.1 MB | 20,283 | 12 | broad_id, pert_iname, qc_incompatible, purity, vendor, catalog_no, vendor_name, expected_mass | Broad Repurposing Hub molecules + SMILES |
| `broad_repurposing_hub_phase_moa_target_info.parquet` | Parquet | 178.1 KB | 6,798 | 6 | pert_iname, clinical_phase, moa, target, disease_area, indication | Broad Repurposing Hub phase/MoA/target info |
| `co-fractionation.parquet` | Parquet | 1.5 MB | 101,325 | 9 | interaction_id, gene_a_id, gene_b_id, experimental_system_type, pubmed_id, organism_id_a, organism_id_b, throughput_type | BioGRID co-fractionation interactions |
| `czi_census_datasets_v4.parquet` | Parquet | 376.4 KB | 1,003 | 20 | Unnamed: 0, soma_joinid, citation, collection_id, collection_name, collection_doi, collection_doi_label, dataset_id | CZI Census single-cell datasets metadata |
| `ddinter_alimentary_tract_metabolism.parquet` | Parquet | 309.0 KB | 56,367 | 5 | DDInterID_A, Drug_A, DDInterID_B, Drug_B, Level | DDInter drug-drug interactions (alimentary) |
| `ddinter_antineoplastic.parquet` | Parquet | 372.1 KB | 65,389 | 5 | DDInterID_A, Drug_A, DDInterID_B, Drug_B, Level | DDInter drug-drug interactions (antineoplastic) |
| `ddinter_antiparasitic.parquet` | Parquet | 55.3 KB | 5,492 | 5 | DDInterID_A, Drug_A, DDInterID_B, Drug_B, Level | DDInter drug-drug interactions (antiparasitic) |
| `ddinter_blood_organs.parquet` | Parquet | 117.2 KB | 15,140 | 5 | DDInterID_A, Drug_A, DDInterID_B, Drug_B, Level | DDInter drug-drug interactions (blood/organs) |
| `ddinter_dermatological.parquet` | Parquet | 167.4 KB | 25,681 | 5 | DDInterID_A, Drug_A, DDInterID_B, Drug_B, Level | DDInter drug-drug interactions (dermatological) |
| `ddinter_hormonal.parquet` | Parquet | 97.1 KB | 11,727 | 5 | DDInterID_A, Drug_A, DDInterID_B, Drug_B, Level | DDInter drug-drug interactions (hormonal) |
| `ddinter_respiratory.parquet` | Parquet | 192.3 KB | 30,563 | 5 | DDInterID_A, Drug_A, DDInterID_B, Drug_B, Level | DDInter drug-drug interactions (respiratory) |
| `ddinter_various.parquet` | Parquet | 106.2 KB | 12,024 | 5 | DDInterID_A, Drug_A, DDInterID_B, Drug_B, Level | DDInter drug-drug interactions (various) |
| `dosage_growth_defect.parquet` | Parquet | 21.6 KB | 1,179 | 9 | interaction_id, gene_a_id, gene_b_id, experimental_system_type, pubmed_id, organism_id_a, organism_id_b, throughput_type | BioGRID dosage growth defect interactions |
| `evebio_assay_table.parquet` | Parquet | 9.7 KB | 171 | 9 | Assay_ID, Mode, Class, Target_ID, Mechanism, Technology, Max_Control, Control_pXC50 | EVEbio assay metadata |
| `evebio_bundle_table.parquet` | Parquet | 5.4 KB | 171 | 5 | Class, Target_ID, Mode, Bundle_ID, Assay_ID | EVEbio bundle metadata |
| `evebio_compound_table.parquet` | Parquet | 117.8 KB | 1,397 | 7 | Compound_ID, Compound, CAS, DrugBank_ID, UNII, Inchikey, Suppliers | EVEbio compound metadata |
| `evebio_control_table.parquet` | Parquet | 362.6 KB | 212,084 | 4 | Assay_ID, Plate_ID, Control, Activity | EVEbio control samples |
| `evebio_detailed_result_table.parquet` | Parquet | 1.9 MB | 238,887 | 31 | Assay_ID, Target_ID, Mode, Compound_ID, Compound, Scr_Observed_Max, Scr_Category_Detailed, Scr_Category_Simplified | EVEbio detailed assay results |
| `evebio_observed_points_table.parquet` | Parquet | 5.7 MB | 2,070,227 | 9 | Assay_ID, Compound_ID, Target_ID, Phase, Mode, Plate_ID, Compound, Concentration | EVEbio observed data points |
| `evebio_summary_result_table.parquet` | Parquet | 1.1 MB | 238,887 | 12 | Assay_ID, Compound_ID, Mode, Target_ID, Compound, Result, OMax, AMax | EVEbio summarized assay results |
| `evebio_target_table.parquet` | Parquet | 6.2 KB | 85 | 5 | Class, Target_ID, Name, Gene, UniProt_ID | EVEbio target metadata |
| `gene_info.parquet` | Parquet | 3.9 MB | 63,086 | 13 | gene_id, transcript_id, chr, gene_start, gene_end, strand, transcript_start, transcript_end | NCBI gene information |
| `genebass_missense_LC_filtered.parquet` | Parquet | 905.3 MB | 26,583,531 | 8 | annotation, Pvalue, Pvalue_Burden, Pvalue_SKAT, BETA_Burden, SE_Burden, gene, pheno_description | GeneBass missense/LC variant associations |
| `genebass_synonymous_filtered.parquet` | Parquet | 890.5 MB | 26,529,562 | 8 | annotation, Pvalue, Pvalue_Burden, Pvalue_SKAT, BETA_Burden, SE_Burden, gene, pheno_description | GeneBass synonymous variant associations |
| `genetic_interaction.parquet` | Parquet | 8.5 MB | 736,749 | 9 | interaction_id, gene_a_id, gene_b_id, experimental_system_type, pubmed_id, organism_id_a, organism_id_b, throughput_type | BioGRID genetic interaction data |
| `gtex_sample_head.parquet` | Parquet | 3.4 KB | 20 | 4 | Description, Tissue, Expression, Gene | GTEx sample metadata (head) |
| `gtex_tissue_gene_tpm.parquet` | Parquet | 10.9 MB | 1,007,910 | 4 | Description, Tissue, Expression, Gene | GTEx tissue-level gene TPM expression |
| `gwas_catalog.parquet` | Parquet | 39.6 MB | 622,784 | 34 | DATE ADDED TO CATALOG, PUBMEDID, FIRST AUTHOR, DATE, JOURNAL, LINK, STUDY, DISEASE/TRAIT | GWAS Catalog variant-trait associations |
| `kg.parquet` | Parquet | 49.9 MB | 8,100,498 | 12 | relation, display_relation, x_index, x_id, x_type, x_name, x_source, y_index | Biomedical knowledge graph (head/relation/tail triples) |
| `marker_celltype.parquet` | Parquet | 73.4 KB | 16 | 5 | Unnamed: 0, cell_type, description, marker_genes, cano_marker_genes | Cell-type marker gene database |
| `miRDB_v6.0_results.parquet` | Parquet | 68.7 MB | 6,831,595 | 4 | miRNA, target_accession, score, target_symbol | miRDB v6.0 miRNA-target predictions |
| `miRTarBase_MicroRNA_Target_Sites.parquet` | Parquet | 286.0 KB | 7,694 | 10 | miRTarBase ID, miRNA, Species (miRNA), Target Gene, Target Gene (Entrez Gene ID), Species (Target Gene), Target Site, Experiments | miRTarBase miRNA target sites |
| `miRTarBase_microRNA_target_interaction.parquet` | Parquet | 4.8 MB | 557,182 | 9 | miRTarBase ID, miRNA, Species (miRNA), Target Gene, Target Gene (Entrez ID), Species (Target Gene), Experiments, Support Type | miRTarBase miRNA-target interactions |
| `mousemine_m1_positional_geneset.parquet` | Parquet | 271.2 KB | 341 | 10 | chromosome_id, collection, systematicName, msigdbURL, exactSource, externalDetailsURL, pmid, geneSymbols | MouseMine M1 positional gene sets |
| `mousemine_m2_curated_geneset.parquet` | Parquet | 1.1 MB | 2,710 | 10 | chromosome_id, collection, systematicName, msigdbURL, exactSource, externalDetailsURL, pmid, geneSymbols | MouseMine M2 curated gene sets |
| `mousemine_m3_regulatory_target_geneset.parquet` | Parquet | 2.0 MB | 2,047 | 10 | chromosome_id, collection, systematicName, msigdbURL, exactSource, externalDetailsURL, pmid, geneSymbols | MouseMine M3 regulatory target gene sets |
| `mousemine_m5_ontology_geneset.parquet` | Parquet | 4.2 MB | 10,678 | 10 | chromosome_id, collection, systematicName, msigdbURL, exactSource, externalDetailsURL, pmid, geneSymbols | MouseMine M5 ontology gene sets |
| `mousemine_m8_celltype_signature_geneset.parquet` | Parquet | 232.4 KB | 233 | 10 | chromosome_id, collection, systematicName, msigdbURL, exactSource, externalDetailsURL, pmid, geneSymbols | MouseMine M8 cell-type signature gene sets |
| `mousemine_mh_hallmark_geneset.parquet` | Parquet | 47.2 KB | 50 | 10 | chromosome_id, collection, systematicName, msigdbURL, exactSource, externalDetailsURL, pmid, geneSymbols | MouseMine MH hallmark gene sets |
| `msigdb_human_c1_positional_geneset.parquet` | Parquet | 269.3 KB | 302 | 10 | chromosome_id, collection, systematicName, msigdbURL, exactSource, externalDetailsURL, pmid, geneSymbols | MSigDB C1 positional gene sets |
| `msigdb_human_c2_curated_geneset.parquet` | Parquet | 3.0 MB | 7,411 | 10 | chromosome_id, collection, systematicName, msigdbURL, exactSource, externalDetailsURL, pmid, geneSymbols | MSigDB C2 curated gene sets |
| `msigdb_human_c3_regulatory_target_geneset.parquet` | Parquet | 4.1 MB | 3,713 | 10 | chromosome_id, collection, systematicName, msigdbURL, exactSource, externalDetailsURL, pmid, geneSymbols | MSigDB C3 regulatory target gene sets |
| `msigdb_human_c3_subset_transcription_factor_targets_from_GTRD.parquet` | Parquet | 2.2 MB | 1,115 | 10 | chromosome_id, collection, systematicName, msigdbURL, exactSource, externalDetailsURL, pmid, geneSymbols | MSigDB C3 TF targets from GTRD |
| `msigdb_human_c4_computational_geneset.parquet` | Parquet | 406.2 KB | 1,006 | 10 | chromosome_id, collection, systematicName, msigdbURL, exactSource, externalDetailsURL, pmid, geneSymbols | MSigDB C4 computational gene sets |
| `msigdb_human_c5_ontology_geneset.parquet` | Parquet | 6.4 MB | 16,107 | 10 | chromosome_id, collection, systematicName, msigdbURL, exactSource, externalDetailsURL, pmid, geneSymbols | MSigDB C5 ontology gene sets |
| `msigdb_human_c6_oncogenic_signature_geneset.parquet` | Parquet | 166.7 KB | 189 | 10 | chromosome_id, collection, systematicName, msigdbURL, exactSource, externalDetailsURL, pmid, geneSymbols | MSigDB C6 oncogenic signature gene sets |
| `msigdb_human_c7_immunologic_signature_geneset.parquet` | Parquet | 5.1 MB | 5,219 | 10 | chromosome_id, collection, systematicName, msigdbURL, exactSource, externalDetailsURL, pmid, geneSymbols | MSigDB C7 immunologic signature gene sets |
| `msigdb_human_c8_celltype_signature_geneset.parquet` | Parquet | 762.5 KB | 840 | 10 | chromosome_id, collection, systematicName, msigdbURL, exactSource, externalDetailsURL, pmid, geneSymbols | MSigDB C8 cell-type signature gene sets |
| `msigdb_human_h_hallmark_geneset.parquet` | Parquet | 45.3 KB | 50 | 10 | chromosome_id, collection, systematicName, msigdbURL, exactSource, externalDetailsURL, pmid, geneSymbols | MSigDB H hallmark gene sets |
| `omim.parquet` | Parquet | 2.1 MB | 18,637 | 14 | Chromosome, Genomic Position Start, Genomic Position End, Cyto Location, Computed Cyto Location, MIM Number, Gene/Locus And Other Related Symbols, Gene Name | OMIM gene-disease associations |
| `proteinatlas.parquet` | Parquet | 5.2 MB | 20,162 | 107 | Gene, Gene synonym, Ensembl, Gene description, Uniprot, Chromosome, Position, Protein class | Human Protein Atlas expression data |
| `proximity_label-ms.parquet` | Parquet | 856.1 KB | 79,926 | 9 | interaction_id, gene_a_id, gene_b_id, experimental_system_type, pubmed_id, organism_id_a, organism_id_b, throughput_type | BioGRID proximity label MS interactions |
| `reconstituted_complex.parquet` | Parquet | 15.1 KB | 702 | 9 | interaction_id, gene_a_id, gene_b_id, experimental_system_type, pubmed_id, organism_id_a, organism_id_b, throughput_type | BioGRID reconstituted complex interactions |
| `sgRNA_KO_SP_human.parquet` | Parquet | 113.6 MB | 5,259,031 | 11 | Target Gene Symbol, CRISPR Mechanism, sgRNA Sequence, PAM Sequence, On-Target Efficacy Score, Off-Target Rank, Combined Rank, Strand of sgRNA | SpCas9 sgRNA knockout library (human) |
| `sgRNA_KO_SP_mouse.parquet` | Parquet | 112.1 MB | 5,151,163 | 11 | Target Gene Symbol, CRISPR Mechanism, sgRNA Sequence, PAM Sequence, On-Target Efficacy Score, Off-Target Rank, Combined Rank, Strand of sgRNA | SpCas9 sgRNA knockout library (mouse) |
| `synthetic_growth_defect.parquet` | Parquet | 20.6 KB | 1,031 | 9 | interaction_id, gene_a_id, gene_b_id, experimental_system_type, pubmed_id, organism_id_a, organism_id_b, throughput_type | BioGRID synthetic growth defect interactions |
| `synthetic_lethality.parquet` | Parquet | 42.9 KB | 1,909 | 9 | interaction_id, gene_a_id, gene_b_id, experimental_system_type, pubmed_id, organism_id_a, organism_id_b, throughput_type | BioGRID synthetic lethality interactions |
| `synthetic_rescue.parquet` | Parquet | 7.2 KB | 74 | 9 | interaction_id, gene_a_id, gene_b_id, experimental_system_type, pubmed_id, organism_id_a, organism_id_b, throughput_type | BioGRID synthetic rescue interactions |
| `two-hybrid.parquet` | Parquet | 49.2 KB | 3,677 | 9 | interaction_id, gene_a_id, gene_b_id, experimental_system_type, pubmed_id, organism_id_a, organism_id_b, throughput_type | BioGRID two-hybrid interactions |
| `variant_table.parquet` | Parquet | 9.2 MB | 296,143 | 7 | RS, ID, CHR, POS, A1, A2, MAF | Variant annotation table |

## Other Files

| File | Format | Size | Description |
|------|--------|------|-------------|
| `anova_results.csv` | CSV | 62 B | CSV/TSV file (agent-generated, <1KB or not converted) |
| `enamine_cloud_library_smiles.pkl` | PKL | 15.7 KB | Not a DataFrame (list) — kept as PKL |
| `eno1_tumor_normal_values.txt` | TXT | 0 B | Text file |
| `genebass_pLoF_filtered.pkl` | PKL | 571.3 MB | Corrupt/truncated PKL — could not convert (truncated/corrupt file) |
| `go-plus.json` | JSON | 129.9 MB | Gene Ontology (JSON) |
| `gtex_sample.csv` | CSV | 577 B | CSV/TSV file (agent-generated, <1KB or not converted) |
| `heart_gene_correlation.csv` | CSV | 179 B | CSV/TSV file (agent-generated, <1KB or not converted) |
| `heart_gene_correlation_heatmap.png` | PNG | 87.9 KB | Image file |
| `heart_gene_expression.csv` | CSV | 65 B | CSV/TSV file (agent-generated, <1KB or not converted) |
| `heart_gene_expression_bar.png` | PNG | 71.5 KB | Image file |
| `hp.obo` | OBO | 10.1 MB | Ontology (OBO format) |
| `stub1_vs_hsp90aa1_scatter.png` | PNG | 80.7 KB | Image file |
| `stub1_vs_hsp90ab1_scatter.png` | PNG | 85.7 KB | Image file |
| `tpm_ln.csv` | CSV | 74 B | CSV/TSV file (agent-generated, <1KB or not converted) |
| `tpm_log2.csv` | CSV | 0 B | CSV/TSV file (agent-generated, <1KB or not converted) |
| `txgnn_name_mapping.pkl` | PKL | 1.6 MB | Not a DataFrame (dict) — kept as PKL |
| `txgnn_prediction.pkl` | PKL | 68.3 MB | Not a DataFrame (dict) — kept as PKL |

## Archived Originals

Original CSV/TSV/TXT source files have been moved to `csv_originals/` after successful
Parquet conversion. They are retained for reference but are **not** used by the agent.
To access them: `pd.read_csv('csv_originals/<filename>', ...)`

## Conversion Notes

- `genebass_pLoF_filtered.pkl` — corrupt/truncated pickle, could not be loaded
- `gwas_catalog.pkl` — converted with object→string coercion for mixed-type columns
- `txgnn_prediction.pkl`, `txgnn_name_mapping.pkl` — Python dicts, kept as PKL
- `enamine_cloud_library_smiles.pkl` — Python list of SMILES strings, kept as PKL

