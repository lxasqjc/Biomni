#!/bin/bash

# IBD Research Questions Execution Script
# Generated from IBD_Research_Questions.md
# This script runs each research question sequentially through Biomni API

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to execute a research question
execute_research() {
    local question="$1"
    local filename="$2"
    local category="$3"
    
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} Starting: ${YELLOW}$category${NC}"
    echo -e "${BLUE}Question:${NC} $question"
    echo -e "${BLUE}Output file:${NC} logs/$filename.log"
    echo ""
    
    # Execute the curl command and wait for completion
    curl -s -X POST "http://alan:8009/chat" \
      -H "Content-Type: application/json" \
      -d "{
        \"prompt\": \"Analyze all IBD data (that are reasonable to you) under ./data/biomni_data/ibd_sim to answer: $question\"
      }" | jq -r '.response' > "logs/$filename.log" 2>&1
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} Completed: $filename"
    else
        echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} Failed: $filename (exit code: $exit_code)"
    fi
    
    echo "----------------------------------------"
    echo ""
}

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  IBD Research Questions Execution${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if Biomni API is running
echo -e "${BLUE}Checking Biomni API status...${NC}"
if curl -s http://alan:8009/health >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Biomni API is running${NC}"
else
    echo -e "${RED}✗ Biomni API is not accessible at alan:8009${NC}"
    echo -e "${RED}Please start the Biomni service first${NC}"
    exit 1
fi
echo ""

# Start execution
start_time=$(date '+%Y-%m-%d %H:%M:%S')
echo -e "${GREEN}Starting execution at: $start_time${NC}"
echo ""

# 1. MECHANISM PAIRING OPTIMIZATION
echo -e "${YELLOW}=== 🧠 MECHANISM PAIRING OPTIMIZATION ===${NC}"

execute_research \
"Analyze the molecular pathways targeted by current IBD therapies (anti-TNF, JAK inhibitors, integrin antagonists) and identify potential synergistic combinations based on pathway crosstalk" \
"01_molecular_pathways_synergistic_combinations" \
"Combination Therapy Discovery"

execute_research \
"What are the biological rationales for combining specific mechanism classes in IBD? Extract evidence from literature about successful and failed combination attempts" \
"02_biological_rationales_combination_mechanisms" \
"Combination Therapy Discovery"

execute_research \
"Using systems biology approaches, predict which drug mechanism pairs might achieve additive or synergistic effects in mucosal healing" \
"03_systems_biology_drug_mechanism_pairs" \
"Combination Therapy Discovery"

execute_research \
"Identify novel therapeutic targets that could complement existing anti-TNF therapy based on pathway analysis and drug repurposing databases" \
"04_novel_targets_anti_TNF_complement" \
"Combination Therapy Discovery"

execute_research \
"Map the inflammatory cascade in Crohn's disease and identify intervention points where dual targeting could break positive feedback loops" \
"05_inflammatory_cascade_dual_targeting" \
"Mechanistic Interaction Modeling"

execute_research \
"Analyze biomarker data to understand which combination therapies show evidence of pathway modulation beyond single agents" \
"06_biomarker_combination_therapy_evidence" \
"Mechanistic Interaction Modeling"

execute_research \
"What molecular signatures predict response to combination vs. monotherapy in IBD patients?" \
"07_molecular_signatures_combination_vs_mono" \
"Mechanistic Interaction Modeling"

# 2. PATIENT STRATIFICATION & ENRICHMENT
echo -e "${YELLOW}=== 🔍 PATIENT STRATIFICATION & ENRICHMENT ===${NC}"

execute_research \
"Develop a predictive model for Histologic Endoscopic Mucosal Improvement (HEMI) using clinical, endoscopic, and biomarker data from IBD patients" \
"08_HEMI_predictive_model" \
"HEMI Prediction Models"

execute_research \
"What baseline patient characteristics (demographics, disease history, biomarkers) best predict achievement of complete disease clearance?" \
"09_baseline_characteristics_disease_clearance" \
"HEMI Prediction Models"

execute_research \
"Analyze the IBD simulation dataset to identify distinct patient phenotypes based on response patterns to different therapeutic approaches" \
"10_patient_phenotypes_response_patterns" \
"HEMI Prediction Models"

execute_research \
"Create a risk stratification model to identify patients likely to achieve deep remission vs. those requiring combination therapy" \
"11_risk_stratification_deep_remission" \
"HEMI Prediction Models"

execute_research \
"Build an enrichment strategy to identify Crohn's patients at high risk for rapid fibrotic progression using baseline clinical and molecular data" \
"12_enrichment_fibrotic_progression" \
"Rapid Progression Identification"

execute_research \
"What early warning biomarkers can predict patients who will progress from inflammatory to stricturing disease behavior?" \
"13_early_warning_biomarkers_stricturing" \
"Rapid Progression Identification"

execute_research \
"Analyze patterns in disease trajectory data to identify critical time windows for intervention before irreversible fibrosis develops" \
"14_disease_trajectory_intervention_windows" \
"Rapid Progression Identification"

execute_research \
"Develop a predictive algorithm for fibrosis development using disease duration, anatomical location, treatment history, and genetic factors" \
"15_fibrosis_predictive_algorithm" \
"Fibrosis Risk Assessment"

execute_research \
"What combination of clinical variables, biomarkers, and imaging features best identifies patients suitable for anti-fibrotic therapy trials?" \
"16_anti_fibrotic_trial_patient_identification" \
"Fibrosis Risk Assessment"

# 3. OUTCOME PREDICTION & TRIAL SIMULATION
echo -e "${YELLOW}=== 🧪 OUTCOME PREDICTION & TRIAL SIMULATION ===${NC}"

execute_research \
"Simulate clinical trial outcomes for different combination therapy strategies using patient trajectory modeling from real-world IBD datasets" \
"17_clinical_trial_simulation_combination_therapy" \
"Clinical Trial Design Optimization"

execute_research \
"What sample sizes and trial durations are needed to detect clinically meaningful differences in HEMI endpoints for different patient subgroups?" \
"18_sample_sizes_HEMI_endpoints" \
"Clinical Trial Design Optimization"

execute_research \
"Model the impact of different enrichment strategies on trial success probability and timeline for fibrotic Crohn's studies" \
"19_enrichment_strategies_fibrotic_trials" \
"Clinical Trial Design Optimization"

execute_research \
"Compare different histologic scoring systems (RHI, Nancy Index) and their correlation with clinical outcomes to recommend standardized HEMI criteria" \
"20_histologic_scoring_systems_comparison" \
"Endpoint Harmonization"

execute_research \
"Analyze the relationship between endoscopic healing, histologic remission, and long-term clinical outcomes to validate composite endpoints" \
"21_endoscopic_histologic_outcomes_relationship" \
"Endpoint Harmonization"

execute_research \
"What is the optimal combination of clinical, endoscopic, and histologic criteria that best predicts sustained remission?" \
"22_optimal_criteria_sustained_remission" \
"Endpoint Harmonization"

execute_research \
"Analyze FDA and EMA guidance documents to understand evolving regulatory expectations for IBD trials and identify key evidence requirements" \
"23_regulatory_guidance_IBD_trials" \
"Regulatory Pathway Analysis"

execute_research \
"What evidence packages are needed to support approval of combination therapies vs. novel single agents in IBD?" \
"24_evidence_packages_combination_vs_single" \
"Regulatory Pathway Analysis"

# 4. DATA MINING & PREDICTIVE ANALYTICS
echo -e "${YELLOW}=== 📊 DATA MINING & PREDICTIVE ANALYTICS ===${NC}"

execute_research \
"Mine existing IBD registries and clinical databases to identify predictors of treatment response that weren't captured in original clinical trials" \
"25_registry_mining_treatment_predictors" \
"Real-World Evidence Analysis"

execute_research \
"What real-world treatment sequences show the best long-term outcomes for maintaining deep remission?" \
"26_treatment_sequences_deep_remission" \
"Real-World Evidence Analysis"

execute_research \
"Analyze prescription patterns and outcomes data to identify optimal timing for treatment escalation or combination initiation" \
"27_prescription_patterns_treatment_timing" \
"Real-World Evidence Analysis"

execute_research \
"Integrate multi-omics data (genomics, proteomics, transcriptomics) from the IBD dataset to identify novel predictive biomarkers for therapy response" \
"28_multi_omics_predictive_biomarkers" \
"Biomarker Discovery"

execute_research \
"What inflammatory and fibrotic pathway signatures correlate with response to different mechanism classes?" \
"29_pathway_signatures_mechanism_response" \
"Biomarker Discovery"

execute_research \
"Develop a composite biomarker panel that can guide personalized treatment selection in IBD" \
"30_composite_biomarker_panel" \
"Biomarker Discovery"

execute_research \
"Systematically analyze potential confounders (disease duration, age at onset, anatomical extent) that may influence fibrosis associations in IBD studies" \
"31_confounders_fibrosis_associations" \
"Confounding Factor Analysis"

execute_research \
"What statistical approaches best control for treatment duration and disease heterogeneity when modeling fibrosis outcomes?" \
"32_statistical_approaches_fibrosis_modeling" \
"Confounding Factor Analysis"

# 5. PRECISION MEDICINE APPLICATIONS
echo -e "${YELLOW}=== 🎯 PRECISION MEDICINE APPLICATIONS ===${NC}"

execute_research \
"Based on patient characteristics and response patterns, what is the optimal treatment algorithm for newly diagnosed Crohn's disease patients?" \
"33_optimal_treatment_algorithm_new_patients" \
"Treatment Sequencing Optimization"

execute_research \
"Analyze treatment failure patterns to identify when combination therapy should be initiated vs. switching to a different mechanism" \
"34_treatment_failure_combination_timing" \
"Treatment Sequencing Optimization"

execute_research \
"What factors predict primary vs. secondary loss of response, and how should this influence treatment selection?" \
"35_primary_secondary_loss_response" \
"Treatment Sequencing Optimization"

execute_research \
"Develop patient-specific risk calculators that weigh efficacy potential against safety risks for different therapeutic approaches" \
"36_patient_specific_risk_calculators" \
"Personalized Risk-Benefit Assessment"

execute_research \
"What clinical decision support tools would help gastroenterologists optimize treatment choices based on individual patient profiles?" \
"37_clinical_decision_support_tools" \
"Personalized Risk-Benefit Assessment"

# 6. ADVANCED ANALYTICS & AI APPLICATIONS
echo -e "${YELLOW}=== 🔬 ADVANCED ANALYTICS & AI APPLICATIONS ===${NC}"

execute_research \
"Develop deep learning models to quantify fibrosis from endoscopic or cross-sectional imaging and correlate with histologic scores" \
"38_deep_learning_fibrosis_imaging" \
"Deep Learning for Image Analysis"

execute_research \
"What imaging biomarkers can predict response to anti-fibrotic therapies before histologic changes are apparent?" \
"39_imaging_biomarkers_anti_fibrotic_response" \
"Deep Learning for Image Analysis"

execute_research \
"Extract insights from clinical notes and pathology reports to identify subtle patterns associated with treatment response or disease progression" \
"40_clinical_notes_NLP_insights" \
"Natural Language Processing"

execute_research \
"What clinical language patterns in provider notes correlate with subsequent treatment outcomes?" \
"41_language_patterns_treatment_outcomes" \
"Natural Language Processing"

execute_research \
"Build disease progression networks to understand how different IBD phenotypes transition over time and identify intervention opportunities" \
"42_disease_progression_networks" \
"Network Analysis"

execute_research \
"What patient similarity networks can guide treatment selection based on outcomes in comparable patients?" \
"43_patient_similarity_networks" \
"Network Analysis"

# 7. META-ANALYSIS & SYSTEMATIC REVIEW
echo -e "${YELLOW}=== 📝 META-ANALYSIS & SYSTEMATIC REVIEW ===${NC}"

execute_research \
"Conduct a systematic review and meta-analysis of all published combination therapy trials in IBD to identify success patterns and failure modes" \
"44_systematic_review_combination_trials" \
"Literature Synthesis"

execute_research \
"What are the key predictors of combination therapy success across different studies and patient populations?" \
"45_predictors_combination_therapy_success" \
"Literature Synthesis"

execute_research \
"Analyze the evolution of clinical trial endpoints in IBD and their correlation with real-world outcomes" \
"46_trial_endpoints_evolution_correlation" \
"Literature Synthesis"

execute_research \
"Compare the effectiveness of different therapeutic sequences (step-up vs. top-down vs. accelerated step-up) using real-world evidence" \
"47_therapeutic_sequences_effectiveness" \
"Comparative Effectiveness"

execute_research \
"What combination strategies show the best risk-adjusted outcomes across different IBD phenotypes?" \
"48_combination_strategies_risk_adjusted" \
"Comparative Effectiveness"

# Summary
end_time=$(date '+%Y-%m-%d %H:%M:%S')
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Execution Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${BLUE}Start time:${NC} $start_time"
echo -e "${BLUE}End time:${NC} $end_time"
echo -e "${BLUE}Total questions processed:${NC} 48"
echo -e "${BLUE}Logs location:${NC} ./logs/"
echo ""
echo -e "${YELLOW}To view results:${NC}"
echo "ls -la logs/"
echo "cat logs/01_molecular_pathways_synergistic_combinations.log"
echo ""
echo -e "${YELLOW}To check PDF outputs:${NC}"
echo "curl -s http://alan:8009/outputs | jq"