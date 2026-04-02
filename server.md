# clean all in one launch for wagner
export http_proxy=
export https_proxy="http://emeapzen.astrazeneca.net:9480"
export HTTP_PROXY=
export HTTPS_PROXY="http://emeapzen.astrazeneca.net:9480"
export NO_PROXY="10.0.0.0/8,172.29.0.0/8,astrazeneca.net,*.astrazeneca.net,vllm.paas-jade.astrazeneca.net,localhost,127.0.0.1"
export no_proxy="10.0.0.0/8,172.29.0.0/8,astrazeneca.net,*.astrazeneca.net,vllm.paas-jade.astrazeneca.net,localhost,127.0.0.1"
cd /alan-data/jinc/git_chen/Biomni && conda activate biomni_e1

# NOTE: All commands use `systemd-run --user --scope` to run in an
# independent systemd scope (cgroup). This ensures processes survive
# tmux session crashes — setsid/nohup alone is NOT enough because
# systemd kills all processes in the tmux cgroup scope when tmux dies.
#
# To list running biomni services:  systemctl --user list-units 'biomni-*'
# To stop a specific service:       systemctl --user stop biomni-8010.scope
# To stop all biomni services:      systemctl --user stop 'biomni-*.scope'
#
# RESTART PATTERN: Each for-loop uses this 3-step pattern per port:
#   1. lsof + kill -9  — force-kill any process on the port (instant)
#   2. systemctl reset-failed — clear stale/failed scope so the unit name can be reused
#   3. systemd-run — launch new process in a fresh scope
# If scopes get stuck with 0 tasks, run: systemctl --user daemon-reload

cd /alan-data/jinc/git_chen/Biomni && conda activate biomni_e1
systemd-run --user --scope --unit=biomni-httpd bash -c 'cd /alan-data/jinc/git_chen/Biomni/local_outputs && exec python -m http.server 8100' > /dev/null 2>&1 &

lsof -t -i :8009 | xargs kill -9

systemd-run --user --scope --unit=biomni-8009 bash -c 'exec uvicorn biomni_api_server_qwen3_next_80b_auto_clean_azimuth:app --host 0.0.0.0 --port 8009 > /alan-data/jinc/git_chen/Biomni/logs/biomni_api_server_qwen3_next_80b_auto_clean_azimuth.log 2>&1' &

systemd-run --user --scope --unit=biomni-8020 bash -c 'exec uvicorn biomni_api_server_qwen3_next_80b_auto_clean_azimuth:app --host 0.0.0.0 --port 8020 > /alan-data/jinc/git_chen/Biomni/logs/biomni_api_server_qwen3_next_80b_auto_clean_azimuth_8020_2.log 2>&1' &

for port in {8010..8041}; do
  systemd-run --user --scope --unit=biomni-$port bash -c "exec uvicorn biomni_api_server_qwen3_next_80b_auto_clean_azimuth:app --host 0.0.0.0 --port $port > /alan-data/jinc/git_chen/Biomni/logs/biomni_api_server_qwen3_next_80b_auto_clean_azimuth_$port.log 2>&1" &
done

lsof -t -i :8012 | xargs kill -9
systemd-run --user --scope --unit=biomni-8012 bash -c 'exec uvicorn biomni_api_server_qwen3_next_80b_auto_clean_azimuth:app --host 0.0.0.0 --port 8012 > /alan-data/jinc/git_chen/Biomni/logs/biomni_api_server_qwen3_next_80b_auto_clean_azimuth_8012.log 2>&1' &

for port in {8020..8041}; do
  pid=$(lsof -t -i :$port 2>/dev/null) && [ -n "$pid" ] && kill -9 $pid 2>/dev/null; systemctl --user reset-failed biomni-$port.scope 2>/dev/null
  systemd-run --user --scope --unit=biomni-$port bash -c "exec uvicorn biomni_api_server_qwen3_next_80b_auto_clean_azimuth:app --host 0.0.0.0 --port $port > /alan-data/jinc/git_chen/Biomni/logs/biomni_api_server_qwen3_next_80b_auto_clean_azimuth_$port.log 2>&1" &
done








for port in {8010..8022}; do
  pid=$(lsof -t -i :$port 2>/dev/null) && [ -n "$pid" ] && kill -9 $pid 2>/dev/null; systemctl --user reset-failed biomni-$port.scope 2>/dev/null
  systemd-run --user --scope --unit=biomni-$port bash -c "exec uvicorn biomni_api_server_qwen3_next_80b_auto_clean_azimuth:app --host 0.0.0.0 --port $port > /alan-data/jinc/git_chen/Biomni/logs/biomni_api_server_qwen3_next_80b_auto_clean_azimuth_$port.log 2>&1" &
done

# Qwen-3.5-35B-AWQ-4bit (no thinking)

lsof -t -i :9020 | xargs kill -9
BIOMNI_MODEL="Qwen-3.5-35B-AWQ-4bit" BIOMNI_ENABLE_THINKING=true \
     systemd-run --user --scope --unit=biomni-9020 bash -c 'exec uvicorn biomni_api_server_qwen3_5_35B_azimuth:app --host 0.0.0.0 --port 9020 > /alan-data/jinc/git_chen/Biomni/logs/biomni_api_server_qwen3_5_35B_azimuth_no_think_9020.log 2>&1' &

BIOMNI_MODEL="Qwen-3.5-35B-AWQ-4bit" BIOMNI_ENABLE_THINKING=true
for port in {9020..9030}; do
  systemd-run --user --scope --unit=biomni-$port bash -c "exec uvicorn biomni_api_server_qwen3_5_35B_azimuth:app --host 0.0.0.0 --port $port > /alan-data/jinc/git_chen/Biomni/logs/biomni_api_server_qwen3_5_35B_azimuth_no_think_$port.log 2>&1" &
done
BIOMNI_MODEL="Qwen-3.5-35B-AWQ-4bit" BIOMNI_ENABLE_THINKING=true
for port in {9031..9040}; do
  systemd-run --user --scope --unit=biomni-$port bash -c "exec uvicorn biomni_api_server_qwen3_5_35B_azimuth:app --host 0.0.0.0 --port $port > /alan-data/jinc/git_chen/Biomni/logs/biomni_api_server_qwen3_5_35B_azimuth_no_think_$port.log 2>&1" &
done


for port in {7020..7030}; do
  pid=$(lsof -t -i :$port 2>/dev/null) && [ -n "$pid" ] && kill -9 $pid 2>/dev/null; systemctl --user reset-failed biomni-$port.scope 2>/dev/null
  systemd-run --user --scope --unit=biomni-$port bash -c "exec uvicorn biomni_api_server_qwen3_5_35B_azimuth:app --host 0.0.0.0 --port $port > /alan-data/jinc/git_chen/Biomni/logs/biomni_api_server_qwen3_5_35B_azimuth_$port.log 2>&1" &
done

for port in {7020..7040}; do
  pid=$(lsof -t -i :$port 2>/dev/null) && [ -n "$pid" ] && kill -9 $pid 2>/dev/null; systemctl --user reset-failed biomni-$port.scope 2>/dev/null
  systemd-run --user --scope --unit=biomni-$port bash -c "exec uvicorn biomni_api_server_qwen3_5_35B_azimuth:app --host 0.0.0.0 --port $port > /alan-data/jinc/git_chen/Biomni/logs/biomni_api_server_qwen3_5_35B_azimuth_$port.log 2>&1" &
done


# test with thinking:
curl -X POST http://localhost:7020/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "hello", "chat_template_kwargs": {"enable_thinking": true}}'

# test without thinking:
curl -X POST http://localhost:9020/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "hello", "chat_template_kwargs": {"enable_thinking": false}}'

# Qwen3.5-25B (UD_Q6_K_XL.gguf) on ludwig drylab 
for port in {7015..7018}; do
  systemd-run --user --scope --unit=biomni-$port bash -c "exec uvicorn biomni_api_server_qwen3_5_25B_drylab:app --host 0.0.0.0 --port $port > /alan-data/jinc/git_chen/Biomni/logs/biomni_api_server_qwen3_5_25B_drylab_$port.log 2>&1" &
done

# Qwen3-Coder-Next-AWQ-4bit on Azimuth
for port in {7020..7030}; do
  pid=$(lsof -t -i :$port 2>/dev/null) && [ -n "$pid" ] && kill -9 $pid 2>/dev/null; systemctl --user reset-failed biomni-$port.scope 2>/dev/null
  systemd-run --user --scope --unit=biomni-$port bash -c "exec uvicorn biomni_api_server_qwen3_coder_next_awq_4b_azimuth:app --host 0.0.0.0 --port $port > /alan-data/jinc/git_chen/Biomni/logs/biomni_api_server_qwen3_coder_next_awq_4b_azimuth_$port.log 2>&1" &
done

# Qwen3-Next-80B AWQ-4bit on http://alan:5401/v1
for port in {7031..7040}; do
  pid=$(lsof -t -i :$port 2>/dev/null) && [ -n "$pid" ] && kill -9 $pid 2>/dev/null; systemctl --user reset-failed biomni-$port.scope 2>/dev/null
  systemd-run --user --scope --unit=biomni-$port bash -c "exec uvicorn biomni_api_server_qwen3next_80b_awq4b_drylab:app --host 0.0.0.0 --port $port > /alan-data/jinc/git_chen/Biomni/logs/biomni_api_server_qwen3next_80b_awq4b_drylab_$port.log 2>&1" &
done

# scp Qwen--Qwen3-Next-80B-A3B-Instruct
BIOMNI_MODEL="/home/jovyan/vol-1/root_chen/git_chen/data/models_chen/.cache/huggingface/hub/models--Qwen--Qwen3-Next-80B-A3B-Instruct/snapshots/b8bdf23cb031b0364158445817f675436f2482ed" BIOMNI_BASE_URL="http://semlscpg002.scp.astrazeneca.net:8000/v1" \
     systemd-run --user --scope --unit=biomni-6020 bash -c 'exec uvicorn biomni_api_server_qwen3next_80b_awq4b_drylab:app --host 0.0.0.0 --port 6020 > /alan-data/jinc/git_chen/Biomni/logs/biomni_api_server_qwen3_next_80b_a3b_scp_6020.log 2>&1' &

# semlscpg001
export BIOMNI_MODEL="/home/jovyan/vol-1/root_chen/git_chen/data/models_chen/.cache/huggingface/hub/models--Qwen--Qwen3-Next-80B-A3B-Instruct/snapshots/b8bdf23cb031b0364158445817f675436f2482ed" 
export BIOMNI_BASE_URL="http://semlscpg001.scp.astrazeneca.net:8000/v1"

for port in {6000..6010}; do
  pid=$(lsof -t -i :$port 2>/dev/null) && [ -n "$pid" ] && kill -9 $pid 2>/dev/null; systemctl --user reset-failed biomni-$port.scope 2>/dev/null
  systemd-run --user --scope --unit=biomni-$port bash -c "exec uvicorn biomni_api_server_qwen3next_80b_awq4b_drylab:app --host 0.0.0.0 --port $port > /alan-data/jinc/git_chen/Biomni/logs/biomni_api_server_qwen3_next_80b_a3b_scp_semlscpg001_$port.log 2>&1" &
done

BIOMNI_MODEL="/home/jovyan/vol-1/root_chen/git_chen/data/models_chen/.cache/huggingface/hub/models--Qwen--Qwen3-Next-80B-A3B-Instruct/snapshots/b8bdf23cb031b0364158445817f675436f2482ed" BIOMNI_BASE_URL="http://semlscpg002.scp.astrazeneca.net:8000/v1"
for port in {6011..6019}; do
  systemd-run --user --scope --unit=biomni-$port bash -c "exec uvicorn biomni_api_server_qwen3next_80b_awq4b_drylab:app --host 0.0.0.0 --port $port > /alan-data/jinc/git_chen/Biomni/logs/biomni_api_server_qwen3_next_80b_a3b_scp_$port.log 2>&1" &
done

# semlscpg002
export BIOMNI_MODEL="/home/jovyan/vol-1/root_chen/git_chen/data/models_chen/.cache/huggingface/hub/models--Qwen--Qwen3-Next-80B-A3B-Instruct/snapshots/b8bdf23cb031b0364158445817f675436f2482ed" 
export BIOMNI_BASE_URL="http://semlscpg002.scp.astrazeneca.net:8000/v1"

for port in {6020..6029}; do
  pid=$(lsof -t -i :$port 2>/dev/null) && [ -n "$pid" ] && kill -9 $pid 2>/dev/null; systemctl --user reset-failed biomni-$port.scope 2>/dev/null
  systemd-run --user --scope --unit=biomni-$port bash -c "exec uvicorn biomni_api_server_qwen3next_80b_awq4b_drylab:app --host 0.0.0.0 --port $port > /alan-data/jinc/git_chen/Biomni/logs/biomni_api_server_qwen3_next_80b_a3b_scp_semlscpg002_$port.log 2>&1" &
done

# semlscpg003
export BIOMNI_MODEL="/home/jovyan/vol-1/root_chen/git_chen/data/models_chen/.cache/huggingface/hub/models--Qwen--Qwen3-Next-80B-A3B-Instruct/snapshots/b8bdf23cb031b0364158445817f675436f2482ed" 
export BIOMNI_BASE_URL="http://semlscpg003.scp.astrazeneca.net:8000/v1"

for port in {6030..6039}; do
  pid=$(lsof -t -i :$port 2>/dev/null) && [ -n "$pid" ] && kill -9 $pid 2>/dev/null; systemctl --user reset-failed biomni-$port.scope 2>/dev/null
  systemd-run --user --scope --unit=biomni-$port bash -c "exec uvicorn biomni_api_server_qwen3next_80b_awq4b_drylab:app --host 0.0.0.0 --port $port > /alan-data/jinc/git_chen/Biomni/logs/biomni_api_server_qwen3_next_80b_a3b_scp_semlscpg003_$port.log 2>&1" &
done

# semlscpg005
export BIOMNI_MODEL="/home/jovyan/vol-1/root_chen/git_chen/data/models_chen/.cache/huggingface/hub/models--Qwen--Qwen3-Next-80B-A3B-Instruct/snapshots/b8bdf23cb031b0364158445817f675436f2482ed" 
export BIOMNI_BASE_URL="http://semlscpg005.scp.astrazeneca.net:8000/v1"

for port in {6050..6059}; do
  pid=$(lsof -t -i :$port 2>/dev/null) && [ -n "$pid" ] && kill -9 $pid 2>/dev/null; systemctl --user reset-failed biomni-$port.scope 2>/dev/null
  systemd-run --user --scope --unit=biomni-$port bash -c "exec uvicorn biomni_api_server_qwen3next_80b_awq4b_drylab:app --host 0.0.0.0 --port $port > /alan-data/jinc/git_chen/Biomni/logs/biomni_api_server_qwen3_next_80b_a3b_scp_semlscpg005_$port.log 2>&1" &
done

# semlscpg006
export BIOMNI_MODEL="/home/jovyan/vol-1/root_chen/git_chen/data/models_chen/.cache/huggingface/hub/models--Qwen--Qwen3-Next-80B-A3B-Instruct/snapshots/b8bdf23cb031b0364158445817f675436f2482ed"
export BIOMNI_BASE_URL="http://semlscpg006.scp.astrazeneca.net:8000/v1"

for port in {6060..6069}; do
  pid=$(lsof -t -i :$port 2>/dev/null) && [ -n "$pid" ] && kill -9 $pid 2>/dev/null; systemctl --user reset-failed biomni-$port.scope 2>/dev/null
  systemd-run --user --scope --unit=biomni-$port bash -c "exec uvicorn biomni_api_server_qwen3next_80b_awq4b_drylab:app --host 0.0.0.0 --port $port > /alan-data/jinc/git_chen/Biomni/logs/biomni_api_server_qwen3_next_80b_a3b_scp_semlscpg006_$port.log 2>&1" &
done

# semlscpg007
export BIOMNI_MODEL="/home/jovyan/vol-1/root_chen/git_chen/data/models_chen/.cache/huggingface/hub/models--Qwen--Qwen3-Next-80B-A3B-Instruct/snapshots/b8bdf23cb031b0364158445817f675436f2482ed" 
export BIOMNI_BASE_URL="http://semlscpg007.scp.astrazeneca.net:8000/v1"

for port in {6070..6079}; do
  pid=$(lsof -t -i :$port 2>/dev/null) && [ -n "$pid" ] && kill -9 $pid 2>/dev/null; systemctl --user reset-failed biomni-$port.scope 2>/dev/null
  systemd-run --user --scope --unit=biomni-$port bash -c "exec uvicorn biomni_api_server_qwen3next_80b_awq4b_drylab:app --host 0.0.0.0 --port $port > /alan-data/jinc/git_chen/Biomni/logs/biomni_api_server_qwen3_next_80b_a3b_scp_semlscpg007_$port.log 2>&1" &
done

# semlscpg008
export BIOMNI_MODEL="/home/jovyan/vol-1/root_chen/git_chen/data/models_chen/.cache/huggingface/hub/models--Qwen--Qwen3-Next-80B-A3B-Instruct/snapshots/b8bdf23cb031b0364158445817f675436f2482ed" 
export BIOMNI_BASE_URL="http://semlscpg008.scp.astrazeneca.net:8000/v1"
for port in {6080..6089}; do
  systemd-run --user --scope --unit=biomni-$port bash -c "exec uvicorn biomni_api_server_qwen3next_80b_awq4b_drylab:app --host 0.0.0.0 --port $port > /alan-data/jinc/git_chen/Biomni/logs/biomni_api_server_qwen3_next_80b_a3b_scp_semlscpg008_$port.log 2>&1" &
done

# semlscpg009
export BIOMNI_MODEL="/home/jovyan/vol-1/root_chen/git_chen/data/models_chen/.cache/huggingface/hub/models--Qwen--Qwen3-Next-80B-A3B-Instruct/snapshots/b8bdf23cb031b0364158445817f675436f2482ed" 
export BIOMNI_BASE_URL="http://semlscpg009.scp.astrazeneca.net:8000/v1"

for port in {6090..6099}; do
  pid=$(lsof -t -i :$port 2>/dev/null) && [ -n "$pid" ] && kill -9 $pid 2>/dev/null; systemctl --user reset-failed biomni-$port.scope 2>/dev/null
  systemd-run --user --scope --unit=biomni-$port bash -c "exec uvicorn biomni_api_server_qwen3next_80b_awq4b_drylab:app --host 0.0.0.0 --port $port > /alan-data/jinc/git_chen/Biomni/logs/biomni_api_server_qwen3_next_80b_a3b_scp_semlscpg009_$port.log 2>&1" &
done

# semlscpg012
export BIOMNI_MODEL="/home/jovyan/vol-1/root_chen/git_chen/data/models_chen/.cache/huggingface/hub/models--Qwen--Qwen3-Next-80B-A3B-Instruct/snapshots/b8bdf23cb031b0364158445817f675436f2482ed" 
export BIOMNI_BASE_URL="http://semlscpg012.scp.astrazeneca.net:8000/v1"

for port in {6120..6129}; do
  pid=$(lsof -t -i :$port 2>/dev/null) && [ -n "$pid" ] && kill -9 $pid 2>/dev/null; systemctl --user reset-failed biomni-$port.scope 2>/dev/null
  systemd-run --user --scope --unit=biomni-$port bash -c "exec uvicorn biomni_api_server_qwen3next_80b_awq4b_drylab:app --host 0.0.0.0 --port $port > /alan-data/jinc/git_chen/Biomni/logs/biomni_api_server_qwen3_next_80b_a3b_scp_semlscpg012_$port.log 2>&1" &
done


 am initialising another agnet under /alan-data/jinc/git_chen/OpenClaw-RL to work on /alan-data/jinc/git_chen/OpenClaw-RL/DEV_DOCS/CONTEXT/PROJECT_GOAL.md, so will be some connection to DR-Tulu, i want you to write /alan-data/jinc/git_chen/OpenClaw-RL/DEV_DOCS/CONTEXT/DRTULU_AGENT_MESSAGE.md, to summarise important message you'd like to pass on
  to the new agent, it could include but not limit to e.g. summary of DR-Tulu api implementation, key goal, lesson so far, design, as well as practical bit like api set up note etc

curl -s http://alan:6001/ibd-data-info | jq .

curl -s -X POST "http://alan:6020/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Plan a CRISPR screen to identify genes that regulate T cell exhaustion, generate 32 genes that maximize the perturbation effect."
  }' 


curl -s http://alan:8009/ibd-data-info | jq .

curl -s http://alan:8012/ibd-data-info | jq .

curl -k -X POST 'https://wagner-test-biomni.cai.astrazeneca.net/v1/query' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "what data do you have access to",
  "timeout": 600,
  "save_pdf": false,
  "llm": {
    "base_url": "https://vllm.paas-jade.astrazeneca.net/v1",
    "api_key": "natura15tup1d1ty",
    "model_name": "Qwen/Qwen3-Next-80B-A3B-Instruct-FP8",
    "temperature": 0.7
  }
}'


curl -s http://alan:8014/examples | jq '.examples[]' | tail -3

curl -s -X POST "http://alan:8014/chat" \
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


nohup curl -s -X POST "http://alan:8009/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Analyze all IBD data (that are reasonable to you) under ./data/biomni_data/ibd_clean_xavier to answer: Analyze the molecular pathways targeted by current IBD therapies (anti-TNF, JAK inhibitors, integrin antagonists) and identify potential synergistic combinations based on pathway crosstalk"
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

# olga
research_question="do we have fibroblast activation protein (FAP)expressed in all patients with diagnosed fibrosis (in tissue)? There is some literature that suggest that TWIST1 (expressed in blood) may be a biomarker for FAP, it's something that we could possibly check"

nohup curl -s -X POST "http://alan:8009/chat" \
  -H "Content-Type: application/json" \
    -d "{
      \"prompt\": \"Analyze all IBD data (that are reasonable to you) under ./data/biomni_data/ibd_clean_xavier to answer: ${research_question}. Please follow these guidelines: 1) Create and stick to your initial analysis plan throughout the process. 2) Aim to produce a comprehensive report at the end - either print it directly as markdown format or save it as a separate .md file. 3) Be transparent and honest about your methodology, data sources, and any limitations. Clearly indicate when you're using biomni's local data versus your own knowledge base versus external references. If any analysis attempts fail, explain what went wrong and what alternative approaches you're trying.\"
    }" | jq -r '.response' | head -20 > logs/fap_twist1_analysis.log 2>&1 &

# ricardo
research_question="predict the label macroscopic_appearance label using proteomics data and identify top proteins? Data should be matched on locations and timepoints."

nohup curl -s -X POST "http://alan:8009/chat" \
  -H "Content-Type: application/json" \
    -d "{
      \"prompt\": \"Analyze all IBD data (that are reasonable to you) under ./data/biomni_data/ibd_clean_xavier to answer: ${research_question}. Please follow these guidelines: 1) Create and stick to your initial analysis plan throughout the process. 2) Aim to produce a comprehensive report at the end - either print it directly as markdown format or save it as a separate .md file. 3) Be transparent and honest about your methodology, data sources, and any limitations. Clearly indicate when you're using biomni's local data versus your own knowledge base versus external references. If any analysis attempts fail, explain what went wrong and what alternative approaches you're trying.\"
    }" | jq -r '.response' | head -20 > logs/marco_appearance_analysis.log 2>&1 &

# ricardo
research_question="Analyze all IBD data (that are reasonable to you) under ./data/biomni_data/ibd_clean_xavier to predict the label macroscopic_appearance label using proteomics data and identify top proteins? Data should be matched on locations and timepoints."

nohup curl -s -X POST "http://alan:8009/chat" \
  -H "Content-Type: application/json" \
    -d "{
      \"prompt\": \"Analyze all IBD data (that are reasonable to you) under ./data/biomni_data/ibd_clean_xavier to answer: predict the label macroscopic_appearance label using proteomics data and identify top proteins? Data should be matched on locations and timepoints."
    }" | jq -r '.response' | head -20 > logs/marco_appearance_analysis.log 2>&1 &


# xavier - FIXED VERSION
# The issue was multiline string with quotes causing JSON parsing problems

nohup curl -s -X POST "http://alan:8009/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a clean Kaplan-Meier survival dataset for IBD time-to-surgery analysis. Data Sources (from ./data/biomni_data/ibd_clean_xavier/redshift_data/raw_tables/): ibd_21183_procedures_emr.csv (identify IBD surgeries - event=1, censored=0), ibd_21183_diagnosis_emr.csv (diagnosis date - follow-up start), ibd_21183_demographics.csv (baseline covariates: age, sex, disease type, smoking), ibd_21183_labs_emr.csv (time-varying lab results), ibd_21183_prescriptions_emr.csv (time-varying medications). Requirements: Consistent patient IDs across files, valid date handling and standardized time units, output format: one row/patient (baseline) OR multiple rows/patient (time-varying) with columns: patient_id, start_time, stop_time, event, covariates. Deliverables: Clean survival dataset and summary report with file descriptions, cleaning steps/assumptions, dataset statistics (n patients, n events, median follow-up, missing data rates). Scope: Use only the specified 5 files. Please follow these guidelines: 1) Create and stick to your initial analysis plan throughout the process. 2) Aim to produce a comprehensive report at the end - either print it directly as markdown format or save it as a separate .md file. 3) Be transparent and honest about your methodology, data sources, and any limitations. Clearly indicate when you are using biomnis local data versus your own knowledge base versus external references. If any analysis attempts fail, explain what went wrong and what alternative approaches you are trying."
  }' | jq -r '.response' > logs/xavier_kaplan_meier_survival_analysis.log 2>&1 &




Use IBD data under /alan-data/jinc/git_chen/Biomni/data/biomni_data/ibd_clean_xavier

Train an RF model to predict the label "disease_activity_60" from proteomics data, taking only patients with Crohn's disease. 
 
First, locate the key files for this analysis: GSF1618983_NPX_below_lod_included.gct (proteomics data with expression values and SampleIDs), omics_samples.csv (contains the label disease_activity_60, patient IDs and dates and disease locations). 
 
Use these files to successfully merge the labels data with the proteomics expression, matching on patient IDs and dates. Then, map the values of "disease_activity_60" to 0 (remission or mild) or 1 (otherwise). You should then split into 3 sub datasets based on the disease_location (ileal, ileocolonic and colonic) and within each dataset train an RF model to predict the binarized disease_activity_60. Use 5 fold cross validation with splits at the patient level.
 
Finally, produce a plot of the top 15 important features for prediction in the RF model by using SHAP analysis. If possible, find out the biological significance of these predictors and how they relate to Crohn's disease.
 