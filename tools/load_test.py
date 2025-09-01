#!/usr/bin/env python3
"""
Load Testing Script for Spotify App Agent Template

This script performs comprehensive load testing on the Spotify bot
to ensure it can handle various load scenarios and API rate limits.

LEARNING OBJECTIVES:
- Understand load testing principles and methodologies
- Learn about API rate limiting and backoff strategies
- Practice performance testing and optimization
- Understand stress testing and failure scenarios
- Learn about monitoring and metrics collection during load tests
"""

import time
import threading
import requests
import json
import statistics
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import sys
import os
from typing import Dict, List, Tuple, Optional
import random

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from spotify_client import SpotifyClient


class LoadTester:
    """Load testing framework for Spotify bot."""
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        """Initialize the load tester."""
        self.base_url = base_url
        self.results = {
            'requests': [],
            'errors': [],
            'start_time': None,
            'end_time': None
        }
        self.lock = threading.Lock()
        
        # Test scenarios
        self.scenarios = {
            'light': {'users': 5, 'requests_per_user': 10, 'delay': 1.0},
            'medium': {'users': 15, 'requests_per_user': 20, 'delay': 0.5},
            'heavy': {'users': 30, 'requests_per_user': 50, 'delay': 0.2},
            'stress': {'users': 50, 'requests_per_user': 100, 'delay': 0.1}
        }
    
    def make_request(self, endpoint: str, method: str = 'GET', data: Optional[Dict] = None) -> Dict:
        """Make a single HTTP request and record metrics."""
        start_time = time.time()
        
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method.upper() == 'GET':
                response = requests.get(url, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            end_time = time.time()
            duration = end_time - start_time
            
            result = {
                'endpoint': endpoint,
                'method': method,
                'status_code': response.status_code,
                'duration': duration,
                'timestamp': datetime.now().isoformat(),
                'success': 200 <= response.status_code < 300
            }
            
            with self.lock:
                self.results['requests'].append(result)
            
            return result
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            error_result = {
                'endpoint': endpoint,
                'method': method,
                'status_code': None,
                'duration': duration,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            }
            
            with self.lock:
                self.results['errors'].append(error_result)
            
            return error_result
    
    def test_endpoint(self, endpoint: str, method: str = 'GET', data: Optional[Dict] = None) -> Dict:
        """Test a specific endpoint."""
        return self.make_request(endpoint, method, data)
    
    def test_dashboard_endpoints(self) -> List[Dict]:
        """Test all dashboard endpoints."""
        endpoints = [
            ('/', 'GET'),
            ('/analytics', 'GET'),
            ('/config', 'GET'),
            ('/logs', 'GET'),
            ('/api/status', 'GET'),
            ('/api/playlists', 'GET'),
            ('/api/analytics', 'GET'),
            ('/health', 'GET'),
            ('/metrics', 'GET')
        ]
        
        results = []
        for endpoint, method in endpoints:
            result = self.test_endpoint(endpoint, method)
            results.append(result)
            time.sleep(0.1)  # Small delay between requests
        
        return results
    
    def test_spotify_api_endpoints(self, spotify_client: SpotifyClient) -> List[Dict]:
        """Test Spotify API endpoints through the client."""
        results = []
        
        # Test user playlists
        try:
            start_time = time.time()
            playlists = spotify_client.get_user_playlists()
            end_time = time.time()
            
            results.append({
                'endpoint': 'spotify_user_playlists',
                'method': 'GET',
                'status_code': 200,
                'duration': end_time - start_time,
                'timestamp': datetime.now().isoformat(),
                'success': True,
                'playlist_count': len(playlists.get('items', []))
            })
        except Exception as e:
            results.append({
                'endpoint': 'spotify_user_playlists',
                'method': 'GET',
                'status_code': None,
                'duration': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
        
        # Test playlist tracks (if we have a playlist)
        try:
            if playlists and playlists.get('items'):
                playlist_id = playlists['items'][0]['id']
                start_time = time.time()
                tracks = spotify_client.get_playlist_tracks(playlist_id)
                end_time = time.time()
                
                results.append({
                    'endpoint': 'spotify_playlist_tracks',
                    'method': 'GET',
                    'status_code': 200,
                    'duration': end_time - start_time,
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'track_count': len(tracks.get('items', []))
                })
        except Exception as e:
            results.append({
                'endpoint': 'spotify_playlist_tracks',
                'method': 'GET',
                'status_code': None,
                'duration': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
        
        return results
    
    def run_concurrent_users(self, num_users: int, requests_per_user: int, delay: float = 0.0) -> List[Dict]:
        """Run concurrent user simulation."""
        print(f"🚀 Starting load test with {num_users} users, {requests_per_user} requests each")
        
        self.results['start_time'] = datetime.now().isoformat()
        
        def user_worker(user_id: int) -> List[Dict]:
            """Worker function for each simulated user."""
            user_results = []
            
            for request_num in range(requests_per_user):
                # Randomly select an endpoint to test
                endpoints = ['/', '/analytics', '/config', '/logs', '/health', '/metrics']
                endpoint = random.choice(endpoints)
                
                result = self.test_endpoint(endpoint)
                user_results.append(result)
                
                if delay > 0:
                    time.sleep(delay)
            
            return user_results
        
        # Run concurrent users
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(user_worker, i) for i in range(num_users)]
            
            for future in as_completed(futures):
                try:
                    user_results = future.result()
                    with self.lock:
                        self.results['requests'].extend(user_results)
                except Exception as e:
                    print(f"❌ Error in user worker: {e}")
        
        self.results['end_time'] = datetime.now().isoformat()
        return self.results['requests']
    
    def run_scenario(self, scenario_name: str) -> Dict:
        """Run a specific load test scenario."""
        if scenario_name not in self.scenarios:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        scenario = self.scenarios[scenario_name]
        print(f"🎯 Running {scenario_name} scenario...")
        
        results = self.run_concurrent_users(
            scenario['users'],
            scenario['requests_per_user'],
            scenario['delay']
        )
        
        return self.analyze_results(scenario_name)
    
    def analyze_results(self, scenario_name: str = "load_test") -> Dict:
        """Analyze test results and generate statistics."""
        if not self.results['requests']:
            return {'error': 'No test results to analyze'}
        
        successful_requests = [r for r in self.results['requests'] if r['success']]
        failed_requests = [r for r in self.results['requests'] if not r['success']]
        
        durations = [r['duration'] for r in successful_requests]
        
        analysis = {
            'scenario': scenario_name,
            'summary': {
                'total_requests': len(self.results['requests']),
                'successful_requests': len(successful_requests),
                'failed_requests': len(failed_requests),
                'success_rate': len(successful_requests) / len(self.results['requests']) * 100 if self.results['requests'] else 0
            },
            'timing': {
                'min_duration': min(durations) if durations else 0,
                'max_duration': max(durations) if durations else 0,
                'mean_duration': statistics.mean(durations) if durations else 0,
                'median_duration': statistics.median(durations) if durations else 0,
                'p95_duration': statistics.quantiles(durations, n=20)[18] if len(durations) >= 20 else max(durations) if durations else 0,
                'p99_duration': statistics.quantiles(durations, n=100)[98] if len(durations) >= 100 else max(durations) if durations else 0
            },
            'endpoints': {},
            'errors': [r['error'] for r in failed_requests if 'error' in r],
            'start_time': self.results['start_time'],
            'end_time': self.results['end_time']
        }
        
        # Group by endpoint
        for request in self.results['requests']:
            endpoint = request['endpoint']
            if endpoint not in analysis['endpoints']:
                analysis['endpoints'][endpoint] = {
                    'total': 0,
                    'successful': 0,
                    'failed': 0,
                    'durations': []
                }
            
            analysis['endpoints'][endpoint]['total'] += 1
            if request['success']:
                analysis['endpoints'][endpoint]['successful'] += 1
                analysis['endpoints'][endpoint]['durations'].append(request['duration'])
            else:
                analysis['endpoints'][endpoint]['failed'] += 1
        
        # Calculate endpoint statistics
        for endpoint, stats in analysis['endpoints'].items():
            if stats['durations']:
                stats['avg_duration'] = statistics.mean(stats['durations'])
                stats['min_duration'] = min(stats['durations'])
                stats['max_duration'] = max(stats['durations'])
            else:
                stats['avg_duration'] = stats['min_duration'] = stats['max_duration'] = 0
        
        return analysis
    
    def print_results(self, analysis: Dict):
        """Print formatted test results."""
        print("\n" + "="*60)
        print(f"📊 LOAD TEST RESULTS - {analysis['scenario'].upper()}")
        print("="*60)
        
        summary = analysis['summary']
        timing = analysis['timing']
        
        print(f"\n📈 SUMMARY:")
        print(f"   Total Requests: {summary['total_requests']}")
        print(f"   Successful: {summary['successful_requests']}")
        print(f"   Failed: {summary['failed_requests']}")
        print(f"   Success Rate: {summary['success_rate']:.2f}%")
        
        print(f"\n⏱️  TIMING (seconds):")
        print(f"   Min: {timing['min_duration']:.3f}")
        print(f"   Max: {timing['max_duration']:.3f}")
        print(f"   Mean: {timing['mean_duration']:.3f}")
        print(f"   Median: {timing['median_duration']:.3f}")
        print(f"   95th Percentile: {timing['p95_duration']:.3f}")
        print(f"   99th Percentile: {timing['p99_duration']:.3f}")
        
        print(f"\n🌐 ENDPOINTS:")
        for endpoint, stats in analysis['endpoints'].items():
            success_rate = (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"   {endpoint}:")
            print(f"     Requests: {stats['total']} (Success: {success_rate:.1f}%)")
            print(f"     Avg Duration: {stats['avg_duration']:.3f}s")
        
        if analysis['errors']:
            print(f"\n❌ ERRORS ({len(analysis['errors'])}):")
            for error in set(analysis['errors'][:5]):  # Show first 5 unique errors
                print(f"   - {error}")
        
        print("\n" + "="*60)
    
    def save_results(self, analysis: Dict, filename: str = None):
        """Save test results to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"load_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        print(f"💾 Results saved to: {filename}")


def main():
    """Main function for load testing."""
    parser = argparse.ArgumentParser(description='Load testing for Spotify App Agent Template')
    parser.add_argument('--scenario', choices=['light', 'medium', 'heavy', 'stress'], 
                       default='medium', help='Load test scenario')
    parser.add_argument('--url', default='http://localhost:5001', 
                       help='Base URL for testing')
    parser.add_argument('--save', action='store_true', 
                       help='Save results to file')
    parser.add_argument('--spotify', action='store_true', 
                       help='Include Spotify API testing')
    
    args = parser.parse_args()
    
    print("🧪 Spotify App Agent Template - Load Testing")
    print("="*50)
    
    # Initialize load tester
    tester = LoadTester(args.url)
    
    try:
        # Run the specified scenario
        results = tester.run_scenario(args.scenario)
        
        # Print results
        tester.print_results(results)
        
        # Save results if requested
        if args.save:
            tester.save_results(results)
        
        # Test Spotify API if requested
        if args.spotify:
            print("\n🎵 Testing Spotify API endpoints...")
            try:
                spotify_client = SpotifyClient()
                spotify_results = tester.test_spotify_api_endpoints(spotify_client)
                
                print(f"✅ Spotify API tests completed: {len(spotify_results)} endpoints tested")
                for result in spotify_results:
                    status = "✅" if result['success'] else "❌"
                    print(f"   {status} {result['endpoint']}: {result['duration']:.3f}s")
                    
            except Exception as e:
                print(f"❌ Spotify API testing failed: {e}")
        
        print("\n🎉 Load testing completed!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Load testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Load testing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
