# clean all in one launch for wagner
export http_proxy=
export https_proxy="http://emeapzen.astrazeneca.net:9480"
export HTTP_PROXY=
export HTTPS_PROXY="http://emeapzen.astrazeneca.net:9480"

cd /alan-data/jinc/git_chen/AGATHA_vllm
conda activate onelink
nohup uvicorn api_server:app --host 0.0.0.0 --port 8006 > agatha.log &

cd /alan-data/jinc/git_chen/Biomni && conda activate biomni_e1
./start_biomni_production.sh

cd /alan-data/jinc/git_chen/Biomni/local_outputs && nohup python -m http.server 8100 > /dev/null 2>&1 &

# done

# Option 1: Quick test of the improved version
cd /alan-data/jinc/git_chen/Biomni && conda activate biomni_e1
nohup uvicorn biomni_api_server_qwen3_30b_auto_clean:app --host 0.0.0.0 --port 8019 > logs/biomni_test.log 2>&1 &

# Option 2: Production deployment (recommended)
./start_biomni_production.sh

# Option 3: Monitor resource usage
python monitor_biomni.py

# Test multiple concurrent requests with different temperatures
for i in {1..2}; do
  curl -X POST "http://alan:8019/chat" \
    -H "Content-Type: application/json" \
    -d '{"prompt": "What is aspirin?"}' &
done
wait

cd /alan-data/jinc/git_chen/Biomni && conda activate biomni_e1
nohup uvicorn biomni_api_server_qwen3_30b_auto_clean_temp:app \
    --host 0.0.0.0 \
    --port 8008 \
    --workers 4 \
    --access-log \
    --log-level info \
    > logs/biomni_uvicorn_temp.log 2>&1 &

# Temperature Control Examples
# Default temperature (0.6)
curl -X POST "http://alan:8008/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is aspirin?"}'

# Low temperature for factual analysis (0.1)
curl -X POST "http://alan:8008/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Analyze the molecular structure of insulin", "temperature": 0.1}'

# Medium temperature for balanced responses (0.6)
curl -X POST "http://alan:8008/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain diabetes treatment options", "temperature": 0.6}'

# High temperature for creative writing (0.9)
curl -X POST "http://alan:8008/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write a creative summary of recent cancer research breakthroughs", "temperature": 0.9}'

# Get examples and temperature guide
curl -s http://alan:8019/examples | jq '.temperature_guide'
curl -s http://alan:8019/examples | jq '.curl_examples'

cd /alan-data/jinc/git_chen/Biomni/local_outputs && nohup python -m http.server 8100 > /dev/null 2>&1 &

lsof -t -i :8009 | xargs kill -9
<!-- nohup uvicorn biomni_api_server:app --host 0.0.0.0 --port 8009 > biomni.log & -->
nohup uvicorn biomni_api_server_qwen3_next_80b_auto_clean_azimuth:app --host 0.0.0.0 --port 8009 > logs/biomni_api_server_qwen3_next_80b_auto_clean_azimuth.log 2>&1 &


<!-- cd /alan-data/jinc/git_chen/Biomni && conda activate biomni_e1 && nohup uvicorn biomni_api_server_qwen3_30b:app --host 0.0.0.0 --port 8009 > biomni_api_server_qwen3_30b.log & -->

nohup uvicorn biomni_api_server_qwen3_next_80b:app --host 0.0.0.0 --port 8010 > biomni_api_server_qwen3_next_80b.log &

curl -s http://alan:8009/ibd-data-info | jq .

curl -s http://alan:8010/ibd-data-info | jq .

curl -s http://alan:8009/examples | jq '.examples[]' | tail -3

curl -s -X POST "http://alan:8009/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "what data are there under biomni_data",
    "save_pdf": false
  }' 

curl -s -X POST "http://alan:8009/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "search: hsa-let-7g-5p miRDB v6.0 target genes",
    "save_pdf": false
  }' 


start_time=$(date +%s)

curl -s -X POST "http://alan:8009/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Plan a CRISPR screen to identify genes that regulate T cell exhaustion, generate 32 genes that maximize the perturbation effect."
  }' 

end_time=$(date +%s)
elapsed=$((end_time - start_time))
echo "Execution time: ${elapsed} seconds"


nohup curl -s -X POST "http://alan:8010/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Analyze all IBD data (that are reasonable to you) under ./data/biomni_data/ibd_sim to answer: Analyze the molecular pathways targeted by current IBD therapies (anti-TNF, JAK inhibitors, integrin antagonists) and identify potential synergistic combinations based on pathway crosstalk"
  }' | jq -r '.response' | head -20 > ibd_molecular_pathways_analysis.log 2>&1 &



curl -s -X POST "http://alan:8010/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Analyze the IBD clinical scores data in ./data/biomni_data/ibd_sim/IBD_meta_data/IBD_clinical_scores.csv to identify patterns and correlations"
  }' | jq -r '.response' | head -20

nohup curl -s -X POST "http://alan:8009/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Analyze all IBD data (that are reasonable to you) under ./data/biomni_data/ibd_sim to find patterns and correlations"
  }' | jq -r '.response' | head -20 > ibd_all_data_analysis.log 2>&1 &

nohup curl -s -X POST "http://alan:8009/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Analyze all IBD data (that are reasonable to you) under ./data/biomni_data/ibd_sim to answer: "
  }' | jq -r '.response' | head -20 > ibd_all_data_analysis.log 2>&1 &

# olga
research_question="do we have fibroblast activation protein (FAP)expressed in all patients with diagnosed fibrosis (in tissue)? There is some literature that suggest that TWIST1 (expressed in blood) may be a biomarker for FAP, it's something that we could possibly check"

nohup curl -s -X POST "http://alan:8010/chat" \
  -H "Content-Type: application/json" \
    -d "{
      \"prompt\": \"Analyze all IBD data (that are reasonable to you) under ./data/biomni_data/ibd_clean_xavier to answer: ${research_question}. Please follow these guidelines: 1) Create and stick to your initial analysis plan throughout the process. 2) Aim to produce a comprehensive report at the end - either print it directly as markdown format or save it as a separate .md file. 3) Be transparent and honest about your methodology, data sources, and any limitations. Clearly indicate when you're using biomni's local data versus your own knowledge base versus external references. If any analysis attempts fail, explain what went wrong and what alternative approaches you're trying.\"
    }" | jq -r '.response' | head -20 > logs/fap_twist1_analysis.log 2>&1 &

# ricardo
research_question="predict the label macroscopic_appearance label using proteomics data and identify top proteins? Data should be matched on locations and timepoints."

nohup curl -s -X POST "http://alan:8010/chat" \
  -H "Content-Type: application/json" \
    -d "{
      \"prompt\": \"Analyze all IBD data (that are reasonable to you) under ./data/biomni_data/ibd_clean_xavier to answer: ${research_question}. Please follow these guidelines: 1) Create and stick to your initial analysis plan throughout the process. 2) Aim to produce a comprehensive report at the end - either print it directly as markdown format or save it as a separate .md file. 3) Be transparent and honest about your methodology, data sources, and any limitations. Clearly indicate when you're using biomni's local data versus your own knowledge base versus external references. If any analysis attempts fail, explain what went wrong and what alternative approaches you're trying.\"
    }" | jq -r '.response' | head -20 > logs/marco_appearance_analysis.log 2>&1 &

# ricardo
research_question="predict the label macroscopic_appearance label using proteomics data and identify top proteins? Data should be matched on locations and timepoints."

nohup curl -s -X POST "http://alan:8010/chat" \
  -H "Content-Type: application/json" \
    -d "{
      \"prompt\": \"Analyze all IBD data (that are reasonable to you) under ./data/biomni_data/ibd_clean_xavier to answer: ${research_question}. Please follow these guidelines: 1) Create and stick to your initial analysis plan throughout the process. 2) Aim to produce a comprehensive report at the end - either print it directly as markdown format or save it as a separate .md file. 3) Be transparent and honest about your methodology, data sources, and any limitations. Clearly indicate when you're using biomni's local data versus your own knowledge base versus external references. If any analysis attempts fail, explain what went wrong and what alternative approaches you're trying.\"
    }" | jq -r '.response' | head -20 > logs/marco_appearance_analysis.log 2>&1 &


# xavier - FIXED VERSION
# The issue was multiline string with quotes causing JSON parsing problems

nohup curl -s -X POST "http://alan:8010/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a clean Kaplan-Meier survival dataset for IBD time-to-surgery analysis. Data Sources (from ./data/biomni_data/ibd_clean_xavier/redshift_data/raw_tables/): ibd_21183_procedures_emr.csv (identify IBD surgeries - event=1, censored=0), ibd_21183_diagnosis_emr.csv (diagnosis date - follow-up start), ibd_21183_demographics.csv (baseline covariates: age, sex, disease type, smoking), ibd_21183_labs_emr.csv (time-varying lab results), ibd_21183_prescriptions_emr.csv (time-varying medications). Requirements: Consistent patient IDs across files, valid date handling and standardized time units, output format: one row/patient (baseline) OR multiple rows/patient (time-varying) with columns: patient_id, start_time, stop_time, event, covariates. Deliverables: Clean survival dataset and summary report with file descriptions, cleaning steps/assumptions, dataset statistics (n patients, n events, median follow-up, missing data rates). Scope: Use only the specified 5 files. Please follow these guidelines: 1) Create and stick to your initial analysis plan throughout the process. 2) Aim to produce a comprehensive report at the end - either print it directly as markdown format or save it as a separate .md file. 3) Be transparent and honest about your methodology, data sources, and any limitations. Clearly indicate when you are using biomnis local data versus your own knowledge base versus external references. If any analysis attempts fail, explain what went wrong and what alternative approaches you are trying."
  }' | jq -r '.response' > logs/xavier_kaplan_meier_survival_analysis.log 2>&1 &




