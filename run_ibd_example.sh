#!/bin/bash

# IBD Research Example Script
# Single example execution for testing

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create logs directory if it doesn't exist
mkdir -p logs

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  IBD Research Example Execution${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if Biomni API is running
echo -e "${BLUE}Checking Biomni API status...${NC}"
if curl -s http://localhost:8009/health >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Biomni API is running${NC}"
else
    echo -e "${RED}✗ Biomni API is not accessible at localhost:8009${NC}"
    echo -e "${RED}Please start the Biomni service first${NC}"
    exit 1
fi
echo ""

# Execute the first research question as an example
echo -e "${YELLOW}Executing Example Research Question:${NC}"
echo -e "${BLUE}Question:${NC} Analyze the molecular pathways targeted by current IBD therapies (anti-TNF, JAK inhibitors, integrin antagonists) and identify potential synergistic combinations based on pathway crosstalk"
echo -e "${BLUE}Output file:${NC} logs/example_molecular_pathways.log"
echo ""

start_time=$(date '+%Y-%m-%d %H:%M:%S')
echo -e "${GREEN}Starting execution at: $start_time${NC}"
echo ""

# Execute the curl command
curl -s -X POST "http://localhost:8009/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Analyze all IBD data (that are reasonable to you) under ./data/biomni_data/ibd_sim to answer: Analyze the molecular pathways targeted by current IBD therapies (anti-TNF, JAK inhibitors, integrin antagonists) and identify potential synergistic combinations based on pathway crosstalk"
  }' | jq -r '.response' > logs/example_molecular_pathways.log 2>&1

local_exit_code=$?

end_time=$(date '+%Y-%m-%d %H:%M:%S')

echo ""
if [ $local_exit_code -eq 0 ]; then
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} Completed successfully!"
else
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} Failed (exit code: $local_exit_code)"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Example Execution Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${BLUE}Start time:${NC} $start_time"
echo -e "${BLUE}End time:${NC} $end_time"
echo -e "${BLUE}Output file:${NC} logs/example_molecular_pathways.log"
echo ""

echo -e "${YELLOW}To view the result:${NC}"
echo "cat logs/example_molecular_pathways.log"
echo ""
echo -e "${YELLOW}To check PDF outputs:${NC}"
echo "curl -s http://localhost:8009/outputs | jq"
echo ""
echo -e "${YELLOW}To run the full analysis (48 questions):${NC}"
echo "./run_ibd_research.sh"