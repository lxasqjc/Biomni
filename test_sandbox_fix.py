#!/usr/bin/env python3
"""Test script to verify sandbox implementation works correctly"""
import os
import sys
from datetime import datetime

# Add the biomni directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from biomni.agent import A1

# Test configuration
TEST_CONFIG = {
    'path': './data',
    'llm': 'Qwen/Qwen3-Next-80B-A3B-Instruct-FP8',
    'base_url': 'https://vllm.paas-jade.astrazeneca.net/v1',
    'api_key': 'natura15tup1d1ty',
    'commercial_mode': True
}

# Generate test output folder
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
test_output_folder = f"./local_outputs/test_{timestamp}"

print(f"Testing sandbox implementation...")
print(f"Test output folder: {test_output_folder}")

# Create agent with output_folder
agent = A1(**TEST_CONFIG, output_folder=test_output_folder)

# Test query that creates files
test_query = """
Create a simple test plot and save it as 'test_plot.png', 
and create a small CSV file called 'test_data.csv' with some sample data.
"""

print(f"\nExecuting test query...")
log, response = agent.go(test_query)

print(f"\nResponse: {response[:200]}...")

# Check if files were created in the correct location
print(f"\n--- Verification ---")
if os.path.exists(test_output_folder):
    files = os.listdir(test_output_folder)
    print(f"Files in {test_output_folder}: {files}")
    if files:
        print("✅ SUCCESS: Files were created in the session folder!")
    else:
        print("⚠️ No files found in session folder")
else:
    print(f"❌ FAIL: Output folder {test_output_folder} was not created")

# Check if files leaked to root directory
root_files = [f for f in os.listdir('.') if f.startswith('test_') and (f.endswith('.png') or f.endswith('.csv'))]
if root_files:
    print(f"⚠️ WARNING: Files leaked to root directory: {root_files}")
else:
    print("✅ No files leaked to root directory")
