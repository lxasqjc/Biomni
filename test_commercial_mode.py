#!/usr/bin/env python3
"""
Test script for commercial_mode functionality
"""

def test_commercial_mode():
    """Test the commercial_mode configuration"""
    print("Testing Biomni commercial_mode configuration...")
    
    # Test commercial mode (should exclude non-commercial datasets)
    print("\n1. Testing commercial_mode=True:")
    try:
        from biomni.agent import A1
        agent_commercial = A1(commercial_mode=True, path="./test_data")
        commercial_datasets = len(agent_commercial.data_lake_dict)
        print(f"   ✓ Commercial mode initialized successfully")
        print(f"   ✓ Available datasets: {commercial_datasets}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test academic mode (should include all datasets)
    print("\n2. Testing commercial_mode=False:")
    try:
        agent_academic = A1(commercial_mode=False, path="./test_data")
        academic_datasets = len(agent_academic.data_lake_dict)
        print(f"   ✓ Academic mode initialized successfully")
        print(f"   ✓ Available datasets: {academic_datasets}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Verify that commercial mode has fewer datasets
    if commercial_datasets < academic_datasets:
        excluded_count = academic_datasets - commercial_datasets
        print(f"\n3. Verification:")
        print(f"   ✓ Commercial mode excludes {excluded_count} non-commercial datasets")
        print(f"   ✓ Test passed!")
        return True
    else:
        print(f"\n3. Verification:")
        print(f"   ✗ Expected commercial mode to have fewer datasets")
        return False

if __name__ == "__main__":
    test_commercial_mode()