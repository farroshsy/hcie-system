"""
Research Results API - Expose cold start and experimental data for UI
"""

import json
import logging
import os
import glob
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/research", tags=["research"])

class ResearchResult(BaseModel):
    scenario: str
    convergence_error: float
    final_mastery: float
    expected_mastery: float
    rate_variance: float
    rate_trend: float
    zpd_efficiency: float
    adaptive_rates: List[Optional[float]]
    cold_start_performance: str
    rate_trend_analysis: str
    adaptive_vs_baseline: Dict[str, float]

class ResearchSummary(BaseModel):
    experiment_id: str
    timestamp: str
    total_scenarios: int
    results: List[ResearchResult]
    summary: Dict[str, Any]

@router.get("/cold-start-results")
async def get_cold_start_results() -> Dict[str, Any]:
    """
    Get all cold start research results for UI visualization
    """
    try:
        # Get all research result files
        research_dir = "/app/research_results"
        if not os.path.exists(research_dir):
            return {
                "success": True,
                "data": {
                    "results": [],
                    "summary": {
                        "total_experiments": 0,
                        "latest_timestamp": None,
                        "performance_distribution": {}
                    }
                },
                "message": "No research results found"
            }
        
        # Get latest result file
        pattern = os.path.join(research_dir, "cold_start_results_*.json")
        files = sorted(glob.glob(pattern))
        
        if not files:
            return {
                "success": True,
                "data": {
                    "results": [],
                    "summary": {
                        "total_experiments": 0,
                        "latest_timestamp": None,
                        "performance_distribution": {}
                    }
                },
                "message": "No research result files found"
            }
        
        latest_file = files[-1]
        
        with open(latest_file, 'r') as f:
            data = json.load(f)
        
        # Convert to structured format
        results = []
        performance_dist = {"EXCELLENT": 0, "GOOD": 0, "NEEDS_IMPROVEMENT": 0}
        
        for scenario_name, scenario_data in data.items():
            if isinstance(scenario_data, dict) and 'convergence_error' in scenario_data:
                result = ResearchResult(
                    scenario=scenario_name,
                    convergence_error=scenario_data.get('convergence_error', 0.0),
                    final_mastery=scenario_data.get('final_mastery', 0.0),
                    expected_mastery=scenario_data.get('expected_mastery', 0.0),
                    rate_variance=scenario_data.get('rate_variance', 0.0),
                    rate_trend=scenario_data.get('rate_trend', 0.0),
                    zpd_efficiency=scenario_data.get('zpd_efficiency', 0.0),
                    adaptive_rates=scenario_data.get('adaptive_rates', []),
                    cold_start_performance=scenario_data.get('cold_start_performance', 'UNKNOWN'),
                    rate_trend_analysis=scenario_data.get('rate_trend_analysis', 'UNKNOWN'),
                    adaptive_vs_baseline=scenario_data.get('adaptive_vs_baseline', {})
                )
                results.append(result)
                
                # Count performance distribution
                perf = scenario_data.get('cold_start_performance', 'UNKNOWN')
                if perf in performance_dist:
                    performance_dist[perf] += 1
        
        # Extract timestamp from filename
        timestamp = os.path.basename(latest_file).replace('cold_start_results_', '').replace('.json', '')
        
        return {
            "success": True,
            "data": {
                "results": [result.dict() for result in results],
                "summary": {
                    "total_experiments": len(results),
                    "latest_timestamp": timestamp,
                    "performance_distribution": performance_dist,
                    "file_source": os.path.basename(latest_file)
                }
            },
            "message": f"Loaded {len(results)} research results"
        }
        
    except Exception as e:
        logger.error(f"❌ Error loading research results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load research results: {str(e)}")

@router.get("/cold-start-results/{scenario}")
async def get_scenario_results(scenario: str) -> Dict[str, Any]:
    """
    Get detailed results for a specific scenario
    """
    try:
        # Get latest result file
        research_dir = "/app/research_results"
        pattern = os.path.join(research_dir, "cold_start_results_*.json")
        files = sorted(glob.glob(pattern))
        
        if not files:
            raise HTTPException(status_code=404, detail="No research results found")
        
        latest_file = files[-1]
        
        with open(latest_file, 'r') as f:
            data = json.load(f)
        
        if scenario not in data:
            raise HTTPException(status_code=404, detail=f"Scenario '{scenario}' not found")
        
        scenario_data = data[scenario]
        
        # Add additional analysis
        adaptive_rates = scenario_data.get('adaptive_rates', [])
        if adaptive_rates:
            # Filter out None values
            valid_rates = [r for r in adaptive_rates if r is not None]
            if valid_rates:
                rate_analysis = {
                    "min_rate": min(valid_rates),
                    "max_rate": max(valid_rates),
                    "avg_rate": sum(valid_rates) / len(valid_rates),
                    "rate_std": (sum((r - sum(valid_rates)/len(valid_rates))**2 for r in valid_rates) / len(valid_rates))**0.5,
                    "total_adaptations": len(valid_rates)
                }
            else:
                rate_analysis = {"error": "No valid adaptive rates"}
        else:
            rate_analysis = {"error": "No adaptive rates data"}
        
        return {
            "success": True,
            "data": {
                "scenario": scenario,
                "results": scenario_data,
                "rate_analysis": rate_analysis,
                "mathematical_validation": {
                    "converges": scenario_data.get('convergence_error', 1.0) < 0.2,
                    "adaptive_works": len([r for r in adaptive_rates if r is not None and r != 0.02]) > 0,
                    "stable_trend": abs(scenario_data.get('rate_trend', 0)) < 0.001
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting scenario results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get scenario results: {str(e)}")

@router.get("/export/{format}")
async def export_research_data(format: str = "json") -> Dict[str, Any]:
    """
    Export research data in specified format
    """
    try:
        if format not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")
        
        # Get all research results
        research_dir = "/app/research_results"
        pattern = os.path.join(research_dir, "cold_start_results_*.json")
        files = sorted(glob.glob(pattern))
        
        if not files:
            raise HTTPException(status_code=404, detail="No research results to export")
        
        # Combine all results
        all_results = {}
        for file in files:
            timestamp = os.path.basename(file).replace('cold_start_results_', '').replace('.json', '')
            with open(file, 'r') as f:
                all_results[timestamp] = json.load(f)
        
        if format == "json":
            return {
                "success": True,
                "data": {
                    "export_format": "json",
                    "total_files": len(files),
                    "results": all_results,
                    "exported_at": datetime.utcnow().isoformat()
                }
            }
        else:  # CSV
            # Convert to CSV format (simplified)
            csv_data = "timestamp,scenario,convergence_error,final_mastery,cold_start_performance\n"
            for timestamp, results in all_results.items():
                for scenario, data in results.items():
                    if isinstance(data, dict):
                        csv_data += f"{timestamp},{scenario},{data.get('convergence_error', '')},{data.get('final_mastery', '')},{data.get('cold_start_performance', '')}\n"
            
            return {
                "success": True,
                "data": {
                    "export_format": "csv",
                    "csv_data": csv_data,
                    "exported_at": datetime.utcnow().isoformat()
                }
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error exporting research data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export research data: {str(e)}")

@router.get("/metrics")
async def get_research_metrics() -> Dict[str, Any]:
    """
    Get aggregated research metrics for dashboard
    """
    try:
        # Get latest results
        research_dir = "/app/research_results"
        pattern = os.path.join(research_dir, "cold_start_results_*.json")
        files = sorted(glob.glob(pattern))
        
        if not files:
            return {
                "success": True,
                "data": {
                    "total_experiments": 0,
                    "avg_convergence_error": 0.0,
                    "performance_distribution": {},
                    "adaptive_rate_stats": {}
                }
            }
        
        latest_file = files[-1]
        with open(latest_file, 'r') as f:
            data = json.load(f)
        
        # Calculate metrics
        scenarios = [k for k, v in data.items() if isinstance(v, dict) and 'convergence_error' in v]
        
        convergence_errors = []
        adaptive_rates_all = []
        performance_counts = {"EXCELLENT": 0, "GOOD": 0, "NEEDS_IMPROVEMENT": 0}
        
        for scenario in scenarios:
            scenario_data = data[scenario]
            convergence_errors.append(scenario_data.get('convergence_error', 0.0))
            
            # Collect adaptive rates
            rates = scenario_data.get('adaptive_rates', [])
            adaptive_rates_all.extend([r for r in rates if r is not None])
            
            # Count performance
            perf = scenario_data.get('cold_start_performance', 'UNKNOWN')
            if perf in performance_counts:
                performance_counts[perf] += 1
        
        # Calculate statistics
        avg_convergence = sum(convergence_errors) / len(convergence_errors) if convergence_errors else 0.0
        
        if adaptive_rates_all:
            adaptive_stats = {
                "min_rate": min(adaptive_rates_all),
                "max_rate": max(adaptive_rates_all),
                "avg_rate": sum(adaptive_rates_all) / len(adaptive_rates_all),
                "total_adaptations": len(adaptive_rates_all)
            }
        else:
            adaptive_stats = {}
        
        return {
            "success": True,
            "data": {
                "total_experiments": len(scenarios),
                "avg_convergence_error": avg_convergence,
                "performance_distribution": performance_counts,
                "adaptive_rate_stats": adaptive_stats,
                "latest_timestamp": os.path.basename(latest_file).replace('cold_start_results_', '').replace('.json', '')
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting research metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get research metrics: {str(e)}")
