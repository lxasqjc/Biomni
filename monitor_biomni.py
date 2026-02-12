#!/usr/bin/env python3
"""
Biomni API Server Resource Monitor
Track memory usage and performance metrics
"""

import psutil
import requests
import time
import json
from datetime import datetime

def check_biomni_health():
    """Check if Biomni API is responding"""
    try:
        response = requests.get("http://localhost:8019/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_process_stats():
    """Get memory and CPU stats for Biomni processes"""
    stats = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_percent', 'cpu_percent']):
        try:
            if 'biomni' in ' '.join(proc.info['cmdline']).lower():
                stats.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'memory_percent': proc.info['memory_percent'],
                    'cpu_percent': proc.info['cpu_percent']
                })
        except:
            continue
    return stats

def monitor_loop():
    """Main monitoring loop"""
    print("🔍 Biomni API Server Monitor Started")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Check API health
            is_healthy = check_biomni_health()
            health_status = "✅ HEALTHY" if is_healthy else "❌ DOWN"
            
            # Get system stats
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            
            # Get Biomni process stats
            biomni_processes = get_process_stats()
            
            print(f"\n[{timestamp}] {health_status}")
            print(f"System: CPU {cpu_percent}%, RAM {memory.percent}% ({memory.used//1024//1024} MB used)")
            
            if biomni_processes:
                print("Biomni Processes:")
                total_memory = 0
                for proc in biomni_processes:
                    print(f"  PID {proc['pid']}: {proc['memory_percent']:.1f}% RAM, {proc['cpu_percent']:.1f}% CPU")
                    total_memory += proc['memory_percent']
                print(f"Total Biomni Memory: {total_memory:.1f}%")
            else:
                print("No Biomni processes found")
            
            time.sleep(10)  # Check every 10 seconds
            
    except KeyboardInterrupt:
        print("\n👋 Monitor stopped")

if __name__ == "__main__":
    monitor_loop()