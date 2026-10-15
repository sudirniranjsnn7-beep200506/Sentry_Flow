"""
CICFlowMeter Verification Script

Verifies CICFlowMeter installation and records its interface per TRD §22.2.
This script tests the tool on a sample PCAP and captures all required information
for the verification document.
"""

import subprocess
import sys
import tempfile
from pathlib import Path
from datetime import datetime
import csv

from scapy.all import wrpcap, IP, TCP, UDP, Ether


def create_sample_pcap(output_path: Path) -> Path:
    """
    Create a minimal sample PCAP file for testing.
    
    Creates synthetic traffic with known characteristics:
    - HTTP-like traffic (TCP port 80)
    - DNS-like traffic (UDP port 53)
    
    Args:
        output_path: Path to save the PCAP file
        
    Returns:
        Path to created PCAP file
    """
    print("Creating sample PCAP for testing...")
    
    packets = []
    
    # Simulated HTTP session (forward + backward)
    for i in range(5):
        # Forward packet (client -> server)
        pkt_fwd = Ether()/IP(src="192.168.1.100", dst="192.168.1.1")/TCP(sport=50000+i, dport=80)
        packets.append(pkt_fwd)
        
        # Backward packet (server -> client)
        pkt_bwd = Ether()/IP(src="192.168.1.1", dst="192.168.1.100")/TCP(sport=80, dport=50000+i, flags="A")
        packets.append(pkt_bwd)
    
    # Simulated DNS query
    pkt_dns = Ether()/IP(src="192.168.1.100", dst="8.8.8.8")/UDP(sport=50010, dport=53)
    packets.append(pkt_dns)
    
    # Write to PCAP
    wrpcap(str(output_path), packets)
    print(f"Sample PCAP created: {output_path} ({len(packets)} packets)")
    
    return output_path


def check_cicflowmeter_available() -> tuple:
    """
    Check if cicflowmeter command is available.
    
    Returns:
        Tuple of (available: bool, command: list, error: str)
    """
    print("\n" + "="*70)
    print("CHECKING CICFLOWMETER AVAILABILITY")
    print("="*70)
    
    # Try the .exe in Scripts directory
    venv_exe = Path(sys.executable).parent / "cicflowmeter.exe"
    
    if venv_exe.exists():
        try:
            result = subprocess.run(
                [str(venv_exe), "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"✅ cicflowmeter is available via: {venv_exe}")
                return True, [str(venv_exe)], None
            else:
                print(f"⚠️ cicflowmeter.exe exists but returned non-zero: {result.returncode}")
        except Exception as e:
            print(f"⚠️ Error testing cicflowmeter.exe: {e}")
    
    # Try python -m cicflowmeter
    try:
        result = subprocess.run(
            [sys.executable, "-m", "cicflowmeter", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ cicflowmeter is available via: python -m cicflowmeter")
            return True, [sys.executable, "-m", "cicflowmeter"], None
        else:
            print(f"❌ cicflowmeter returned non-zero: {result.returncode}")
            return False, None, result.stderr
            
    except subprocess.TimeoutExpired:
        print("❌ cicflowmeter command timed out")
        return False, None, "Command timed out"
    except Exception as e:
        print(f"❌ Error checking cicflowmeter: {e}")
        return False, None, str(e)


def get_cicflowmeter_version() -> str:
    """
    Try to get CICFlowMeter version.
    
    Returns:
        Version string or "unknown"
    """
    try:
        import cicflowmeter
        version = getattr(cicflowmeter, '__version__', 'unknown')
        return version
    except:
        return "unknown"


def test_cicflowmeter_execution(pcap_path: Path, output_dir: Path, command: list) -> dict:
    """
    Test CICFlowMeter on a sample PCAP and capture results.
    
    Args:
        pcap_path: Path to input PCAP
        output_dir: Directory for output CSV
        
    Returns:
        Dictionary with test results and metadata
    """
    print("\n" + "="*70)
    print("TESTING CICFLOWMETER EXECUTION")
    print("="*70)
    
    output_csv = output_dir / "test_output.csv"
    
    # Build command (command is already a list)
    full_command = command + [
        "-f", str(pcap_path),
        "-c",
        str(output_csv)
    ]
    
    print(f"\nCommand: {' '.join(full_command)}")
    print(f"Input PCAP: {pcap_path}")
    print(f"Output CSV: {output_csv}")
    
    # Execute
    start_time = datetime.now()
    try:
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            timeout=60
        )
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\nExit code: {result.returncode}")
        print(f"Duration: {duration:.2f} seconds")
        
        if result.stdout:
            print(f"\nStdout:\n{result.stdout}")
        
        if result.stderr:
            print(f"\nStderr:\n{result.stderr}")
        
        # Check if output was created
        if not output_csv.exists():
            print(f"\n❌ Output CSV not created: {output_csv}")
            return {
                "success": False,
                "error": "Output CSV not created",
                "exit_code": result.returncode,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        
        # Read and analyze output
        print(f"\n✅ Output CSV created: {output_csv}")
        
        with open(output_csv, 'r') as f:
            csv_content = f.read()
            
        # Parse CSV header
        csv_lines = csv_content.strip().split('\n')
        if csv_lines:
            header = csv_lines[0]
            columns = header.split(',')
            
            print(f"\nCSV Header (verbatim):")
            print(f"{header}")
            print(f"\nColumn count: {len(columns)}")
            print(f"Row count (including header): {len(csv_lines)}")
            
            # Show first data row if exists
            if len(csv_lines) > 1:
                print(f"\nFirst data row:")
                print(f"{csv_lines[1]}")
            
            return {
                "success": True,
                "exit_code": result.returncode,
                "duration": duration,
                "output_file": str(output_csv),
                "header": header,
                "columns": columns,
                "column_count": len(columns),
                "row_count": len(csv_lines) - 1,  # Exclude header
                "sample_row": csv_lines[1] if len(csv_lines) > 1 else None,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        else:
            print(f"\n❌ Output CSV is empty")
            return {
                "success": False,
                "error": "Output CSV is empty",
                "exit_code": result.returncode,
                "duration": duration
            }
            
    except subprocess.TimeoutExpired:
        print("\n❌ Command timed out (60 seconds)")
        return {
            "success": False,
            "error": "Timeout after 60 seconds",
            "timeout": True
        }
    except Exception as e:
        print(f"\n❌ Error executing cicflowmeter: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def test_empty_pcap_handling(output_dir: Path, command: list) -> dict:
    """
    Test CICFlowMeter behavior with empty PCAP.
    
    Args:
        output_dir: Directory for test files
        
    Returns:
        Dictionary with test results
    """
    print("\n" + "="*70)
    print("TESTING EMPTY PCAP HANDLING")
    print("="*70)
    
    # Create empty PCAP
    empty_pcap = output_dir / "empty.pcap"
    wrpcap(str(empty_pcap), [])
    print(f"Created empty PCAP: {empty_pcap}")
    
    output_csv = output_dir / "empty_output.csv"
    
    full_command = command + [
        "-f", str(empty_pcap),
        "-c", str(output_csv)
    ]
    
    try:
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "exit_code": result.returncode,
            "output_created": output_csv.exists(),
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except Exception as e:
        return {
            "error": str(e)
        }


def main():
    """Main verification routine."""
    print("="*70)
    print("CICFLOWMETER VERIFICATION")
    print("="*70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version}")
    
    # Check availability
    available, command, error = check_cicflowmeter_available()
    
    if not available:
        print("\n" + "="*70)
        print("❌ VERIFICATION FAILED")
        print("="*70)
        print(f"CICFlowMeter is not available or not working")
        if error:
            print(f"Error: {error}")
        sys.exit(1)
    
    # Get version
    version = get_cicflowmeter_version()
    print(f"\nVersion: {version}")
    
    # Create temp directory for tests
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create sample PCAP
        pcap_path = create_sample_pcap(temp_path / "sample.pcap")
        
        # Test execution
        test_results = test_cicflowmeter_execution(pcap_path, temp_path, command)
        
        if not test_results.get("success"):
            print("\n" + "="*70)
            print("❌ VERIFICATION FAILED")
            print("="*70)
            print(f"CICFlowMeter did not produce expected output")
            sys.exit(1)
        
        # Test empty PCAP
        empty_results = test_empty_pcap_handling(temp_path, command)
        
        print("\n" + "="*70)
        print("✅ VERIFICATION SUCCESSFUL")
        print("="*70)
        print(f"\nCICFlowMeter is working correctly")
        print(f"Command: {' '.join(command)}")
        print(f"Version: {version}")
        print(f"Columns extracted: {test_results['column_count']}")
        print(f"Duration on sample PCAP: {test_results['duration']:.2f}s")
        
        # Save verification data for use by verification document
        import json
        verification_data = {
            "verified_at": datetime.now().isoformat(),
            "python_version": sys.version,
            "cicflowmeter_version": version,
            "command": ' '.join(command),
            "command_list": command,
            "test_results": test_results,
            "empty_pcap_results": empty_results
        }
        
        output_file = Path("docs/verification/cicflowmeter_verification_data.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(verification_data, f, indent=2)
        
        print(f"\nVerification data saved to: {output_file}")


if __name__ == '__main__':
    main()
