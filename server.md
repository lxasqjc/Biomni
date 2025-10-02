nohup uvicorn biomni_api_server:app --host 0.0.0.0 --port 8009 > biomni.log &

nohup uvicorn biomni_api_server_qwen3_30b:app --host 0.0.0.0 --port 8009 > biomni_api_server_qwen3_30b.log &

nohup uvicorn biomni_api_server_qwen3_next_80b:app --host 0.0.0.0 --port 8010 > biomni_api_server_qwen3_next_80b.log &

curl -s http://alan:8009/ibd-data-info | jq .

curl -s http://alan:8010/ibd-data-info | jq .

curl -s http://alan:8009/examples | jq '.examples[]' | tail -3

nohup curl -s -X POST "http://alan:8009/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Analyze all IBD data (that are reasonable to you) under ./data/biomni_data/ibd_sim to answer: Analyze the molecular pathways targeted by current IBD therapies (anti-TNF, JAK inhibitors, integrin antagonists) and identify potential synergistic combinations based on pathway crosstalk"
  }' | jq -r '.response' | head -20 > ibd_molecular_pathways_analysis.log 2>&1 &



curl -s -X POST "http://alan:8009/chat" \
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

curl -s -X POST "http://alan:8009/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Analyze all IBD data (that are reasonable to you) under ./data/biomni_data/ibd_sim to answer: {research_question}"
  }' | jq -r '.response' | head -20 > logs/{research_question}.log 2>&1 &