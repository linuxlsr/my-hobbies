#!/usr/bin/env python3
"""Safe load testing for Powerball app without triggering WAF"""

import asyncio
import aiohttp
import time
import json
from datetime import datetime
import statistics

class SafeLoadTester:
    def __init__(self, base_url, max_rps=10):
        self.base_url = base_url
        self.max_rps = max_rps  # Start conservative
        self.results = []
        
    async def make_request(self, session, endpoint, delay=0):
        """Make a single request with optional delay"""
        if delay > 0:
            await asyncio.sleep(delay)
            
        start_time = time.time()
        try:
            async with session.get(f"{self.base_url}{endpoint}") as response:
                end_time = time.time()
                return {
                    'endpoint': endpoint,
                    'status': response.status,
                    'response_time': end_time - start_time,
                    'success': response.status == 200,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            end_time = time.time()
            return {
                'endpoint': endpoint,
                'status': 0,
                'response_time': end_time - start_time,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def gradual_load_test(self):
        """Gradually increase load to find breaking point"""
        
        print("🧪 Starting Safe Load Test")
        print("=" * 50)
        
        # Test endpoints (lightweight first)
        endpoints = ['/ping', '/health', '/api/status']
        
        # Gradual load increase
        load_levels = [1, 2, 5, 10, 15, 20, 25, 30]  # requests per second
        
        async with aiohttp.ClientSession() as session:
            for rps in load_levels:
                print(f"\n📊 Testing {rps} requests/second...")
                
                # Calculate delay between requests
                delay = 1.0 / rps if rps > 0 else 0
                
                # Run for 30 seconds at this load level
                duration = 30
                total_requests = rps * duration
                
                tasks = []
                for i in range(total_requests):
                    endpoint = endpoints[i % len(endpoints)]
                    request_delay = (i / rps)  # Spread requests evenly
                    
                    task = self.make_request(session, endpoint, request_delay)
                    tasks.append(task)
                
                # Execute all requests
                start_test = time.time()
                results = await asyncio.gather(*tasks)
                end_test = time.time()
                
                # Analyze results
                success_count = sum(1 for r in results if r['success'])
                response_times = [r['response_time'] for r in results if r['success']]
                
                if response_times:
                    avg_response = statistics.mean(response_times)
                    p95_response = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
                else:
                    avg_response = 0
                    p95_response = 0
                
                success_rate = (success_count / len(results)) * 100
                actual_rps = len(results) / (end_test - start_test)
                
                print(f"  ✅ Success Rate: {success_rate:.1f}%")
                print(f"  ⏱️  Avg Response: {avg_response:.3f}s")
                print(f"  📈 95th Percentile: {p95_response:.3f}s")
                print(f"  🚀 Actual RPS: {actual_rps:.1f}")
                
                # Store results
                self.results.append({
                    'target_rps': rps,
                    'actual_rps': actual_rps,
                    'success_rate': success_rate,
                    'avg_response_time': avg_response,
                    'p95_response_time': p95_response,
                    'total_requests': len(results)
                })
                
                # Stop if performance degrades significantly
                if success_rate < 95 or avg_response > 5.0:
                    print(f"⚠️  Performance degradation detected at {rps} RPS")
                    break
                
                # Cool down period to avoid triggering WAF
                print("  😴 Cooling down for 10 seconds...")
                await asyncio.sleep(10)
        
        return self.results
    
    def generate_report(self):
        """Generate load test report"""
        
        print("\n📋 LOAD TEST REPORT")
        print("=" * 50)
        
        if not self.results:
            print("No results to report")
            return
        
        print(f"{'RPS':<6} {'Success%':<8} {'Avg(s)':<8} {'P95(s)':<8} {'Status'}")
        print("-" * 50)
        
        max_stable_rps = 0
        
        for result in self.results:
            rps = result['target_rps']
            success = result['success_rate']
            avg_time = result['avg_response_time']
            p95_time = result['p95_response_time']
            
            # Determine status
            if success >= 99 and avg_time < 1.0:
                status = "🟢 Excellent"
                max_stable_rps = rps
            elif success >= 95 and avg_time < 2.0:
                status = "🟡 Good"
                max_stable_rps = rps
            elif success >= 90:
                status = "🟠 Degraded"
            else:
                status = "🔴 Poor"
            
            print(f"{rps:<6} {success:<7.1f}% {avg_time:<7.3f}s {p95_time:<7.3f}s {status}")
        
        print(f"\n🎯 RECOMMENDATIONS:")
        print(f"  Maximum Stable Load: {max_stable_rps} RPS")
        print(f"  Recommended Limit: {int(max_stable_rps * 0.8)} RPS (80% of max)")
        
        # Calculate theoretical concurrent users
        avg_session_time = 30  # seconds
        concurrent_users = max_stable_rps * avg_session_time
        print(f"  Estimated Concurrent Users: ~{concurrent_users}")

async def main():
    # Your deployed app URL
    base_url = "https://avarice.threemoonsnetwork.net"
    
    # Create tester with conservative rate limit
    tester = SafeLoadTester(base_url, max_rps=10)
    
    print("🔒 WAF-Safe Load Testing Strategy:")
    print("  • Gradual load increase")
    print("  • 10-second cool-down periods")
    print("  • Lightweight endpoints only")
    print("  • Max 30 RPS to stay under WAF limits")
    print("  • 30-second test duration per level")
    
    # Run the test
    results = await tester.gradual_load_test()
    
    # Generate report
    tester.generate_report()
    
    # Save results
    with open('load_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to load_test_results.json")

if __name__ == '__main__':
    asyncio.run(main())