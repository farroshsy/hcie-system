#!/usr/bin/env python3
"""
Comprehensive Test Runner
Runs all tests: user lifecycle, security, UX perception, and load testing
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
import subprocess
import sys


class ComprehensiveTestRunner:
    """Runs all test suites and generates comprehensive report"""
    
    def __init__(self):
        self.test_results = {}
        self.base_url = "http://localhost:8001"
        
    async def check_server_health(self) -> bool:
        """Check if the server is running"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health", timeout=10) as response:
                    if response.status == 200:
                        print("Server is healthy")
                        return True
                    else:
                        print(f"Server returned status {response.status}")
                        return False
        except Exception as e:
            print(f"Server health check failed: {e}")
            return False
    
    async def run_user_lifecycle_tests(self) -> Dict:
        """Run user lifecycle tests"""
        print("\n" + "="*60)
        print("RUNNING USER LIFECYCLE TESTS")
        print("="*60)
        
        try:
            # Import and run the test
            from test_user_lifecycle import UserLifecycleTester
            
            async with UserLifecycleTester(self.base_url) as tester:
                result = await tester.run_complete_lifecycle_test()
                self.test_results["user_lifecycle"] = result
                return result
                
        except Exception as e:
            print(f"User lifecycle tests failed: {e}")
            self.test_results["user_lifecycle"] = {
                "success": False,
                "error": str(e),
                "success_rate": 0
            }
            return {"success": False, "error": str(e)}
    
    async def run_security_tests(self) -> Dict:
        """Run security vulnerability tests"""
        print("\n" + "="*60)
        print("RUNNING SECURITY VULNERABILITY TESTS")
        print("="*60)
        
        try:
            from test_security_vulnerabilities import SecurityTester
            
            async with SecurityTester(self.base_url) as tester:
                result = await tester.run_security_tests()
                self.test_results["security"] = result
                return result
                
        except Exception as e:
            print(f"Security tests failed: {e}")
            self.test_results["security"] = {
                "success": False,
                "error": str(e),
                "security_score": 0
            }
            return {"success": False, "error": str(e)}
    
    async def run_ux_tests(self) -> Dict:
        """Run UX perception tests"""
        print("\n" + "="*60)
        print("RUNNING UX PERCEPTION TESTS")
        print("="*60)
        
        try:
            from test_ux_perception import UXPerceptionTester
            
            async with UXPerceptionTester(self.base_url) as tester:
                result = await tester.run_ux_tests()
                self.test_results["ux"] = result
                return result
                
        except Exception as e:
            print(f"UX tests failed: {e}")
            self.test_results["ux"] = {
                "success": False,
                "error": str(e),
                "ux_score": 0
            }
            return {"success": False, "error": str(e)}
    
    async def run_load_tests(self) -> Dict:
        """Run load testing"""
        print("\n" + "="*60)
        print("RUNNING LOAD TESTS")
        print("="*60)
        
        try:
            # Simple load test using the user lifecycle tester
            from test_user_lifecycle import UserLifecycleTester
            
            num_concurrent_users = 20
            print(f"Testing with {num_concurrent_users} concurrent users...")
            
            async def user_session(user_id: int):
                async with UserLifecycleTester(self.base_url) as tester:
                    # Create a simple user and run a short session
                    user = tester.UserSession(
                        user_id=f"load_test_user_{user_id}",
                        email=f"load_test_{user_id}@example.com",
                        password="TestPassword123!"
                    )
                    
                    # Register and run a short session
                    await tester.register_user(user)
                    await tester.login_user(user)
                    
                    # Complete 2-3 tasks
                    for _ in range(3):
                        await tester.get_next_task(user)
                        await tester.submit_answer(user)
                        await asyncio.sleep(0.1)  # Small delay
                    
                    return True
            
            # Run concurrent sessions
            start_time = time.time()
            
            tasks = [user_session(i) for i in range(num_concurrent_users)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            
            successful_sessions = sum(1 for r in results if r is True)
            total_time = end_time - start_time
            
            load_result = {
                "concurrent_users": num_concurrent_users,
                "successful_sessions": successful_sessions,
                "failed_sessions": num_concurrent_users - successful_sessions,
                "success_rate": (successful_sessions / num_concurrent_users) * 100,
                "total_time": total_time,
                "avg_session_time": total_time / num_concurrent_users,
                "requests_per_second": num_concurrent_users / total_time if total_time > 0 else 0
            }
            
            self.test_results["load"] = load_result
            
            print(f"Load Test Results:")
            print(f"  Concurrent Users: {num_concurrent_users}")
            print(f"  Successful Sessions: {successful_sessions}")
            print(f"  Success Rate: {load_result['success_rate']:.1f}%")
            print(f"  Total Time: {total_time:.2f}s")
            print(f"  Requests/sec: {load_result['requests_per_second']:.1f}")
            
            return load_result
            
        except Exception as e:
            print(f"Load tests failed: {e}")
            self.test_results["load"] = {
                "success": False,
                "error": str(e),
                "success_rate": 0
            }
            return {"success": False, "error": str(e)}
    
    def generate_comprehensive_report(self) -> Dict:
        """Generate comprehensive test report"""
        
        # Calculate overall scores
        scores = {}
        
        if "user_lifecycle" in self.test_results:
            scores["user_lifecycle"] = self.test_results["user_lifecycle"].get("success_rate", 0)
        
        if "security" in self.test_results:
            scores["security"] = self.test_results["security"].get("security_score", 0)
        
        if "ux" in self.test_results:
            scores["ux"] = self.test_results["ux"].get("ux_score", 0)
        
        if "load" in self.test_results:
            scores["load"] = self.test_results["load"].get("success_rate", 0)
        
        # Calculate overall score
        if scores:
            overall_score = sum(scores.values()) / len(scores)
        else:
            overall_score = 0
        
        # Determine production readiness
        critical_issues = []
        
        if scores.get("security", 0) < 80:
            critical_issues.append("Security vulnerabilities detected")
        
        if scores.get("user_lifecycle", 0) < 70:
            critical_issues.append("User lifecycle issues")
        
        if scores.get("load", 0) < 60:
            critical_issues.append("Load testing performance issues")
        
        production_ready = len(critical_issues) == 0 and overall_score >= 75
        
        report = {
            "test_summary": {
                "overall_score": overall_score,
                "production_ready": production_ready,
                "critical_issues": critical_issues,
                "test_timestamp": datetime.now().isoformat()
            },
            "individual_scores": scores,
            "detailed_results": self.test_results,
            "recommendations": self.generate_recommendations(scores)
        }
        
        return report
    
    def generate_recommendations(self, scores: Dict) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if scores.get("security", 0) < 80:
            recommendations.extend([
                "Implement proper authentication middleware",
                "Add input validation and sanitization",
                "Implement rate limiting",
                "Fix authorization checks for user data access"
            ])
        
        if scores.get("user_lifecycle", 0) < 70:
            recommendations.extend([
                "Fix token refresh mechanism",
                "Improve session management",
                "Handle edge cases in user registration/login",
                "Improve error handling in task submission"
            ])
        
        if scores.get("ux", 0) < 70:
            recommendations.extend([
                "Adjust task difficulty progression algorithm",
                "Improve feedback clarity and timing",
                "Reduce user frustration indicators",
                "Optimize response time patterns"
            ])
        
        if scores.get("load", 0) < 60:
            recommendations.extend([
                "Optimize database queries",
                "Add caching for frequent requests",
                "Implement connection pooling",
                "Scale horizontally for high load"
            ])
        
        if not recommendations:
            recommendations.append("System appears ready for production deployment")
        
        return recommendations
    
    async def run_all_tests(self) -> Dict:
        """Run all test suites"""
        print("="*80)
        print("COMPREHENSIVE HCIE SYSTEM TESTING")
        print("="*80)
        
        # Check server health first
        if not await self.check_server_health():
            print("Server is not running. Please start the server first:")
            print("  cd RealSystem/HCIE_SYSTEM_BACKENDV2")
            print("  python -m uvicorn app.main:app --host 0.0.0.0 --port 8001")
            return {"error": "Server not running"}
        
        # Run all test suites
        await self.run_user_lifecycle_tests()
        await self.run_security_tests()
        await self.run_ux_tests()
        await self.run_load_tests()
        
        # Generate comprehensive report
        report = self.generate_comprehensive_report()
        
        # Save reports
        with open("comprehensive_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "="*80)
        print("COMPREHENSIVE TEST SUMMARY")
        print("="*80)
        
        print(f"Overall Score: {report['test_summary']['overall_score']:.1f}%")
        print(f"Production Ready: {'YES' if report['test_summary']['production_ready'] else 'NO'}")
        
        if report['test_summary']['critical_issues']:
            print("\nCritical Issues:")
            for issue in report['test_summary']['critical_issues']:
                print(f"  - {issue}")
        
        print("\nIndividual Scores:")
        for test_name, score in report['individual_scores'].items():
            status = "PASS" if score >= 70 else "FAIL"
            print(f"  {test_name.title()}: {score:.1f}% [{status}]")
        
        print("\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  - {rec}")
        
        print(f"\nDetailed report saved to: comprehensive_test_report.json")
        
        return report


async def main():
    """Main test runner"""
    runner = ComprehensiveTestRunner()
    report = await runner.run_all_tests()
    
    # Return success if production ready
    return report.get("test_summary", {}).get("production_ready", False)


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
