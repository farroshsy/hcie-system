"""
Plot Generation Service

Generates publication-ready plots for experiment analysis.
Supports learning curves, regret curves, convergence plots, forest plots, and more.

Design Principles:
- Separate utility module for plot generation
- Supports multiple plot types
- Publication-ready formatting
- Export to PNG/SVG/PDF
"""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import numpy as np
from typing import Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)


class PlotGenerator:
    """
    Generate publication-ready plots for experiment analysis
    
    RESPONSIBILITIES:
    - Generate learning curves
    - Generate regret curves
    - Generate convergence plots
    - Generate forest plots for meta-analysis
    - Export to multiple formats (PNG, SVG, PDF)
    """
    
    def __init__(self, output_dir: str = "plots"):
        """
        Initialize plot generator
        
        Args:
            output_dir: Directory to save plots
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_learning_curves(
        self,
        data: Dict[str, Any],
        title: str = "Learning Curves",
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate learning curves plot
        
        Args:
            data: Data containing learning curves per experiment
            title: Plot title
            output_file: Output file path (auto-generated if not provided)
            
        Returns:
            Path to generated plot file
        """
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Extract learning curves from data
            # Simplified - in reality would parse actual data structure
            experiments = data.get("experiments", {})
            
            for exp_name, exp_data in experiments.items():
                learning_curve = exp_data.get("learning_curve", [])
                if learning_curve:
                    ax.plot(learning_curve, label=exp_name, linewidth=2)
            
            ax.set_xlabel("Interaction Number")
            ax.set_ylabel("Mastery / Learning Gain")
            ax.set_title(title)
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Save plot
            if output_file is None:
                output_file = os.path.join(self.output_dir, "learning_curves.png")
            
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Generated learning curves plot: {output_file}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to generate learning curves plot: {e}")
            raise
    
    def generate_regret_curves(
        self,
        data: Dict[str, Any],
        title: str = "Regret Curves",
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate regret curves plot
        
        Args:
            data: Data containing regret curves per experiment
            title: Plot title
            output_file: Output file path (auto-generated if not provided)
            
        Returns:
            Path to generated plot file
        """
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Extract regret curves from data
            experiments = data.get("experiments", {})
            
            for exp_name, exp_data in experiments.items():
                regret_curve = exp_data.get("regret_curve", [])
                if regret_curve:
                    ax.plot(regret_curve, label=exp_name, linewidth=2)
            
            ax.set_xlabel("Interaction Number")
            ax.set_ylabel("Cumulative Regret")
            ax.set_title(title)
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Save plot
            if output_file is None:
                output_file = os.path.join(self.output_dir, "regret_curves.png")
            
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Generated regret curves plot: {output_file}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to generate regret curves plot: {e}")
            raise
    
    def generate_convergence_plot(
        self,
        data: Dict[str, Any],
        title: str = "Ensemble Convergence",
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate ensemble convergence plot
        
        Args:
            data: Data containing ensemble agreement over time
            title: Plot title
            output_file: Output file path (auto-generated if not provided)
            
        Returns:
            Path to generated plot file
        """
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Extract convergence data
            convergence_data = data.get("convergence", [])
            
            if convergence_data:
                ax.plot(convergence_data, linewidth=2, color='blue')
                ax.fill_between(
                    range(len(convergence_data)),
                    np.array(convergence_data) - 0.1,
                    np.array(convergence_data) + 0.1,
                    alpha=0.3,
                    color='blue'
                )
            
            ax.set_xlabel("Interaction Number")
            ax.set_ylabel("Ensemble Agreement")
            ax.set_title(title)
            ax.grid(True, alpha=0.3)
            
            # Save plot
            if output_file is None:
                output_file = os.path.join(self.output_dir, "convergence_plot.png")
            
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Generated convergence plot: {output_file}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to generate convergence plot: {e}")
            raise
    
    def generate_forest_plot(
        self,
        data: Dict[str, Any],
        title: str = "Meta-Analysis Forest Plot",
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate forest plot for meta-analysis
        
        Args:
            data: Data containing effect sizes and confidence intervals
            title: Plot title
            output_file: Output file path (auto-generated if not provided)
            
        Returns:
            Path to generated plot file
        """
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Extract forest plot data
            studies = data.get("studies", [])
            study_names = [s.get("name", f"Study {i+1}") for i, s in enumerate(studies)]
            effect_sizes = [s.get("effect_size", 0) for s in studies]
            ci_lower = [s.get("ci_lower", 0) for s in studies]
            ci_upper = [s.get("ci_upper", 0) for s in studies]
            
            y_pos = np.arange(len(study_names))
            
            # Plot effect sizes with confidence intervals
            ax.errorbar(
                effect_sizes, y_pos,
                xerr=[np.array(effect_sizes) - np.array(ci_lower),
                      np.array(ci_upper) - np.array(effect_sizes)],
                fmt='o', capsize=5, markersize=8
            )
            
            # Add vertical line at zero
            ax.axvline(x=0, color='red', linestyle='--', alpha=0.5)
            
            ax.set_yticks(y_pos)
            ax.set_yticklabels(study_names)
            ax.set_xlabel("Effect Size")
            ax.set_title(title)
            ax.grid(True, alpha=0.3, axis='x')
            
            # Save plot
            if output_file is None:
                output_file = os.path.join(self.output_dir, "forest_plot.png")
            
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Generated forest plot: {output_file}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to generate forest plot: {e}")
            raise
    
    def generate_jt_trajectory_plot(
        self,
        data: Dict[str, Any],
        title: str = "JT Trajectory",
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate JT trajectory plot
        
        Args:
            data: Data containing JT values over time
            title: Plot title
            output_file: Output file path (auto-generated if not provided)
            
        Returns:
            Path to generated plot file
        """
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Extract JT trajectory data
            jt_trajectory = data.get("jt_trajectory", [])
            
            if jt_trajectory:
                ax.plot(jt_trajectory, linewidth=2, color='green')
            
            ax.set_xlabel("Interaction Number")
            ax.set_ylabel("JT Value")
            ax.set_title(title)
            ax.grid(True, alpha=0.3)
            
            # Save plot
            if output_file is None:
                output_file = os.path.join(self.output_dir, "jt_trajectory.png")
            
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Generated JT trajectory plot: {output_file}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to generate JT trajectory plot: {e}")
            raise


# Example usage
if __name__ == "__main__":
    # Create plot generator
    generator = PlotGenerator()
    
    # Generate sample plots
    sample_data = {
        "experiments": {
            "HCIE": {"learning_curve": [0.1, 0.2, 0.3, 0.4, 0.5]},
            "Random": {"learning_curve": [0.05, 0.1, 0.15, 0.2, 0.25]}
        }
    }
    
    generator.generate_learning_curves(sample_data)
    print("Plot generation test completed!")
