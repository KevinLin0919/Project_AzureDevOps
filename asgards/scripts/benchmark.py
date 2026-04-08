import time
import subprocess
import os
import resource
import statistics
import sys

def benchmark_run(args):
    """Runs a single pass of the script and returns metrics."""
    # We use subprocess to run the script as a separate process to get resource usage
    start_time = time.perf_counter()
    
    # Run the script
    # We'll use resource.getrusage() for the child process if possible, 
    # but simplest for portability in CI is using /usr/bin/time or manually tracking
    
    # Since we want to capture the resource of the child process:
    process = subprocess.Popen([sys.executable, "asgards/src/main.py"] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    end_time = time.perf_counter()
    elapsed = end_time - start_time
    
    # Mocking memory usage and CPU for demonstration in standard Python 
    # (getting precise per-process memory in a portable way across all OS is hard, 
    # so we'll simulate based on resource usage or just use a mock for CI output)
    
    # Real resource usage for this script (which is tiny):
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    
    # Mock Token Count: based on input size (simulated)
    token_count = len(" ".join(args)) * 2 # Mock formula
    
    return {
        "time": elapsed,
        "memory_kb": usage.ru_maxrss,
        "cpu_user": usage.ru_utime,
        "cpu_system": usage.ru_stime,
        "tokens": token_count
    }

def main():
    runs = 5
    args = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
    
    all_metrics = []
    print(f"Starting benchmark for {runs} runs...")
    
    for i in range(runs):
        metrics = benchmark_run(args)
        all_metrics.append(metrics)
        print(f"Run {i+1}: Time={metrics['time']:.4f}s, Memory={metrics['memory_kb']}KB, Tokens={metrics['tokens']}")
        # Short sleep to stabilize
        time.sleep(0.1)

    avg_time = statistics.mean([m['time'] for m in all_metrics])
    avg_mem = statistics.mean([m['memory_kb'] for m in all_metrics])
    avg_cpu = statistics.mean([m['cpu_user'] + m['cpu_system'] for m in all_metrics])
    total_tokens = sum([m['tokens'] for m in all_metrics])

    print("\n" + "="*30)
    print("      BENCHMARK RESULTS      ")
    print("="*30)
    print(f"Average Response Time: {avg_time:.4f}s")
    print(f"Average Memory Usage:  {avg_mem:.2f} KB")
    print(f"Average CPU Time:      {avg_cpu:.4f}s")
    print(f"Total Tokens Used:     {total_tokens}")
    print("="*30)

if __name__ == "__main__":
    main()
