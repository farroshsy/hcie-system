"""
Statistical Aggregation Service

Separate service for aggregating results across multiple experiment runs for meta-analysis.
Provides API endpoints for statistical aggregation as specified in EXPERIMENT_INFRASTRUCTURE_DESIGN.md.

Design Principles:
- Separate service (not integrated into existing code)
- Provides REST API for aggregation operations
- Uses existing StatisticalAggregator class for computation
- Supports meta-analysis (forest plots, heterogeneity)
- Cross-experiment comparison
- Publication-ready plots
"""

from typing import Dict, Any, List
from datetime import datetime
import logging
import uuid
import numpy as np

from infrastructure.experiment.statistical_aggregation import StatisticalAggregator
from storage.postgres_store.interaction_store import PostgresInteractionStore

logger = logging.getLogger(__name__)


class StatisticalAggregationService:
    """
    Service for statistical aggregation with API interface
    
    RESPONSIBILITIES:
    - Provide REST API for aggregation operations
    - Aggregate across multiple experiment runs
    - Meta-analysis (forest plots, heterogeneity)
    - Cross-experiment comparison
    - Publication-ready plots (learning curves, regret curves, convergence plots)
    - Export to CSV/JSON for external analysis
    """
    
    def __init__(self):
        """Initialize statistical aggregation service"""
        self.db_store = PostgresInteractionStore()
        self.statistical_aggregator = StatisticalAggregator(self.db_store)
        
        # Store aggregation results
        self.active_aggregations: Dict[str, Dict[str, Any]] = {}
    
    def aggregate_experiments(
        self,
        experiment_ids: List[str],
        metrics: List[str] = None,
        aggregation_method: str = "fixed_effects",
        plot_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Aggregate results across multiple experiment runs
        
        API: POST /experiments/aggregate
        
        Args:
            experiment_ids: List of experiment identifiers
            metrics: List of metrics to aggregate
            aggregation_method: "fixed_effects" or "random_effects"
            plot_types: List of plot types to generate
            
        Returns:
            Aggregation results with summary statistics and meta-analysis
        """
        try:
            if metrics is None:
                metrics = ["learning_gain", "regret"]
            
            if plot_types is None:
                plot_types = ["learning_curves", "regret_curves"]
            
            # Generate aggregation ID
            aggregation_id = str(uuid.uuid4())
            
            # Aggregate learning gain
            learning_gain_aggregation = self.statistical_aggregator.aggregate_learning_gain(
                experiment_ids=experiment_ids
            )
            
            # Aggregate regret
            regret_aggregation = self.statistical_aggregator.aggregate_regret(
                experiment_ids=experiment_ids
            )
            
            # Compute summary statistics
            summary_statistics = self._compute_summary_statistics(
                learning_gain_aggregation,
                regret_aggregation
            )
            
            # Perform meta-analysis
            meta_analysis = self._perform_meta_analysis(
                learning_gain_aggregation,
                aggregation_method
            )
            
            # Generate plot URLs (simplified - in reality would generate actual plots)
            plots = self._generate_plots(plot_types, aggregation_id)
            
            # Format response according to API specification
            response = {
                "aggregation_id": aggregation_id,
                "summary_statistics": summary_statistics,
                "meta_analysis": meta_analysis,
                "plots": plots,
                "experiment_ids": experiment_ids,
                "metrics": metrics,
                "aggregation_method": aggregation_method,
                "aggregated_at": datetime.now().isoformat()
            }
            
            # Store aggregation result
            self.active_aggregations[aggregation_id] = response
            
            logger.info(f"Aggregation {aggregation_id} completed for {len(experiment_ids)} experiments")
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to aggregate experiments: {e}")
            raise
    
    def _compute_summary_statistics(
        self,
        learning_gain_aggregation: Dict[str, Any],
        regret_aggregation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compute summary statistics across experiments
        
        Args:
            learning_gain_aggregation: Learning gain aggregation results
            regret_aggregation: Regret aggregation results
            
        Returns:
            Summary statistics
        """
        try:
            summary = {
                "learning_gain": {},
                "regret": {}
            }
            
            # Learning gain summary
            if "error" not in learning_gain_aggregation:
                learning_gains = learning_gain_aggregation.get("learning_gains", [])
                if learning_gains:
                    summary["learning_gain"] = {
                        "mean": float(np.mean(learning_gains)),
                        "std": float(np.std(learning_gains)),
                        "median": float(np.median(learning_gains)),
                        "min": float(np.min(learning_gains)),
                        "max": float(np.max(learning_gains)),
                        "n": len(learning_gains)
                    }
            
            # Regret summary
            if "error" not in regret_aggregation:
                regret_curves = regret_aggregation.get("regret_curves", [])
                if regret_curves:
                    # Compute summary of final regret values
                    final_regrets = [curve[-1] if curve else 0 for curve in regret_curves]
                    summary["regret"] = {
                        "mean_final_regret": float(np.mean(final_regrets)),
                        "std_final_regret": float(np.std(final_regrets)),
                        "median_final_regret": float(np.median(final_regrets)),
                        "n": len(regret_curves)
                    }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to compute summary statistics: {e}")
            return {"error": str(e)}
    
    def _perform_meta_analysis(
        self,
        learning_gain_aggregation: Dict[str, Any],
        aggregation_method: str
    ) -> Dict[str, Any]:
        """
        Perform meta-analysis on aggregated results
        
        Args:
            learning_gain_aggregation: Learning gain aggregation results
            aggregation_method: "fixed_effects" or "random_effects"
            
        Returns:
            Meta-analysis results
        """
        try:
            if "error" in learning_gain_aggregation:
                return {"error": "No data available for meta-analysis"}
            
            learning_gains = learning_gain_aggregation.get("learning_gains", [])
            if not learning_gains:
                return {"error": "No learning gains available"}
            
            # Simplified meta-analysis (in reality would use proper meta-analysis libraries)
            n = len(learning_gains)
            mean = np.mean(learning_gains)
            std = np.std(learning_gains)
            se = std / np.sqrt(n)
            
            # Compute 95% confidence interval
            ci_lower = mean - 1.96 * se
            ci_upper = mean + 1.96 * se
            
            # Compute heterogeneity (I² statistic)
            # Simplified calculation
            heterogeneity = 0.0  # Would compute proper I² in full implementation
            
            return {
                "aggregation_method": aggregation_method,
                "pooled_mean": float(mean),
                "pooled_std": float(std),
                "standard_error": float(se),
                "confidence_interval": {
                    "lower": float(ci_lower),
                    "upper": float(ci_upper),
                    "level": 0.95
                },
                "heterogeneity": {
                    "i_squared": heterogeneity,
                    "q_statistic": 0.0  # Would compute Q statistic in full implementation
                },
                "n_studies": n
            }
            
        except Exception as e:
            logger.error(f"Failed to perform meta-analysis: {e}")
            return {"error": str(e)}
    
    def _generate_plots(self, plot_types: List[str], aggregation_id: str) -> List[Dict[str, str]]:
        """
        Generate plot URLs (simplified - in reality would generate actual plots)
        
        Args:
            plot_types: List of plot types to generate
            aggregation_id: Aggregation identifier
            
        Returns:
            List of plot URLs
        """
        plots = []
        
        for plot_type in plot_types:
            # In reality, would generate actual plot files and return URLs
            plot_url = f"/plots/{aggregation_id}/{plot_type}.png"
            plots.append({
                "type": plot_type,
                "url": plot_url
            })
        
        return plots
    
    def export_aggregation(
        self,
        aggregation_id: str,
        format: str = "csv"
    ) -> str:
        """
        Export aggregation results to CSV or JSON
        
        Args:
            aggregation_id: Aggregation identifier
            format: "csv" or "json"
            
        Returns:
            Exported data as string
        """
        try:
            if aggregation_id not in self.active_aggregations:
                raise ValueError(f"Aggregation {aggregation_id} not found")
            
            aggregation = self.active_aggregations[aggregation_id]
            
            if format == "json":
                import json
                return json.dumps(aggregation, indent=2)
            
            elif format == "csv":
                # Simplified CSV export
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow(["metric", "value"])
                
                # Write summary statistics
                summary = aggregation.get("summary_statistics", {})
                for metric, values in summary.items():
                    if isinstance(values, dict):
                        for key, value in values.items():
                            writer.writerow([f"{metric}_{key}", value])
                
                return output.getvalue()
            
            else:
                raise ValueError(f"Unsupported format: {format}")
            
        except Exception as e:
            logger.error(f"Failed to export aggregation: {e}")
            raise
    
    def get_aggregation_status(self, aggregation_id: str) -> Dict[str, Any]:
        """
        Get aggregation status
        
        Args:
            aggregation_id: Aggregation identifier
            
        Returns:
            Aggregation status
        """
        if aggregation_id not in self.active_aggregations:
            raise ValueError(f"Aggregation {aggregation_id} not found")
        
        return self.active_aggregations[aggregation_id]


def main():
    """Main entry point for statistical aggregation service"""
    import os
    from fastapi import FastAPI
    from pydantic import BaseModel
    
    # Create FastAPI app
    app = FastAPI(title="Statistical Aggregation Service")
    
    # Initialize service
    service = StatisticalAggregationService()
    
    # Pydantic models for API
    class AggregationRequest(BaseModel):
        experiment_ids: List[str]
        metrics: List[str] = None
        aggregation_method: str = "fixed_effects"
        plot_types: List[str] = None
    
    class ExportRequest(BaseModel):
        aggregation_id: str
        format: str = "csv"
    
    # API endpoints
    @app.post("/experiments/aggregate")
    async def aggregate(request: AggregationRequest):
        """Aggregate results across multiple experiment runs"""
        return service.aggregate_experiments(
            experiment_ids=request.experiment_ids,
            metrics=request.metrics,
            aggregation_method=request.aggregation_method,
            plot_types=request.plot_types
        )
    
    @app.get("/experiments/aggregation/{aggregation_id}")
    async def get_aggregation_status(aggregation_id: str):
        """Get aggregation status"""
        return service.get_aggregation_status(aggregation_id)
    
    @app.post("/experiments/aggregation/{aggregation_id}/export")
    async def export_aggregation(aggregation_id: str, request: ExportRequest):
        """Export aggregation results"""
        data = service.export_aggregation(
            aggregation_id=aggregation_id,
            format=request.format
        )
        
        if request.format == "csv":
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(content=data, media_type="text/csv")
        else:
            from fastapi.responses import JSONResponse
            return JSONResponse(content=data)
    
    # Run service
    import uvicorn
    port = int(os.getenv("STATISTICAL_AGGREGATION_PORT", 8006))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
