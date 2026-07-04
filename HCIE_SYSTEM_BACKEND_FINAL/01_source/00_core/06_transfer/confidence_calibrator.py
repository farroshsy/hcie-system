"""
Confidence Calibrator - Post-processing layer to calibrate mapping confidence to actual correctness
"""

import numpy as np
from typing import Dict, Any

class ConfidenceCalibrator:
    """
    Calibrates raw confidence scores to match actual correctness rates
    Implements temperature scaling and empirical calibration methods
    """
    
    def __init__(self, method: str = "temperature_scaling"):
        self.method = method
        self.temperature = 1.5  # Default penalizes overconfidence
        self.calibration_data = []
        self.is_calibrated = False
        
    def calibrate_confidence(self, raw_confidence: float) -> float:
        """
        Calibrate a single confidence score
        
        Args:
            raw_confidence: Raw confidence from mapping (0-1)
            
        Returns:
            float: Calibrated confidence (0-1)
        """
        if self.method == "temperature_scaling":
            # Penalize overconfidence: conf^T where T > 1
            calibrated = raw_confidence ** self.temperature
        elif self.method == "linear_scaling":
            # Simple linear reduction
            calibrated = raw_confidence * 0.8
        elif self.method == "empirical" and self.is_calibrated:
            # Use learned calibration curve
            calibrated = self._apply_empirical_calibration(raw_confidence)
        else:
            calibrated = raw_confidence
            
        return np.clip(calibrated, 0.0, 1.0)
    
    def add_calibration_data(self, confidence: float, is_correct: bool):
        """
        Add data point for empirical calibration
        
        Args:
            confidence: Raw confidence score
            is_correct: Actual correctness
        """
        self.calibration_data.append((confidence, is_correct))
        self.is_calibrated = False  # Need to refit
    
    def fit_empirical_calibration(self) -> Dict[str, Any]:
        """
        Fit empirical calibration curve using collected data
        
        Returns:
            Dict with calibration metrics
        """
        if len(self.calibration_data) < 10:
            raise ValueError("Need at least 10 data points for calibration")
        
        # Extract confidence and correctness pairs
        confidences = np.array([pair[0] for pair in self.calibration_data])
        correctness = np.array([pair[1] for pair in self.calibration_data])
        
        # Create confidence bins
        n_bins = 10
        bins = np.linspace(0, 1, n_bins + 1)
        bin_centers = (bins[:-1] + bins[1:]) / 2
        
        # Calculate actual correctness in each bin
        bin_correctness = []
        bin_counts = []
        
        for i in range(n_bins):
            mask = (confidences >= bins[i]) & (confidences < bins[i + 1])
            if np.sum(mask) > 0:
                bin_correctness.append(np.mean(correctness[mask]))
                bin_counts.append(np.sum(mask))
            else:
                bin_correctness.append(0.5)  # Default for empty bins
                bin_counts.append(0)
        
        # Fit calibration curve (simple piecewise linear)
        self.calibration_curve = {
            'bin_centers': bin_centers.tolist(),
            'bin_correctness': bin_correctness,
            'bin_counts': bin_counts
        }
        
        # Calculate calibration error
        calibration_error = np.mean(np.abs(np.array(bin_correctness) - bin_centers))
        
        self.is_calibrated = True
        
        return {
            'calibration_error': calibration_error,
            'n_data_points': len(self.calibration_data),
            'n_bins': n_bins,
            'bins_used': np.sum(np.array(bin_counts) > 0)
        }
    
    def _apply_empirical_calibration(self, raw_confidence: float) -> float:
        """
        Apply learned empirical calibration
        
        Args:
            raw_confidence: Raw confidence score
            
        Returns:
            float: Calibrated confidence
        """
        if not self.is_calibrated:
            return raw_confidence
        
        bin_centers = np.array(self.calibration_curve['bin_centers'])
        bin_correctness = np.array(self.calibration_curve['bin_correctness'])
        
        # Find nearest bin
        idx = np.argmin(np.abs(bin_centers - raw_confidence))
        
        # Return calibrated value with some smoothing
        if idx == 0:
            return bin_correctness[0]
        elif idx == len(bin_centers) - 1:
            return bin_correctness[-1]
        else:
            # Linear interpolation between bins
            x0, x1 = bin_centers[idx-1], bin_centers[idx+1]
            y0, y1 = bin_correctness[idx-1], bin_correctness[idx+1]
            
            if x1 - x0 > 0:
                t = (raw_confidence - x0) / (x1 - x0)
                return y0 + t * (y1 - y0)
            else:
                return bin_correctness[idx]
    
    def get_calibration_metrics(self) -> Dict[str, Any]:
        """
        Get current calibration metrics
        
        Returns:
            Dict with calibration statistics
        """
        if not self.calibration_data:
            return {
                'method': self.method,
                'is_calibrated': False,
                'n_data_points': 0
            }
        
        confidences = np.array([pair[0] for pair in self.calibration_data])
        correctness = np.array([pair[1] for pair in self.calibration_data])
        
        # Current calibration error
        if self.is_calibrated and self.method == "empirical":
            calibration_error = self.calibration_curve.get('calibration_error', 0.0)
        else:
            # Simple calibration error estimate
            calibration_error = np.mean(np.abs(confidences - correctness))
        
        return {
            'method': self.method,
            'is_calibrated': self.is_calibrated,
            'n_data_points': len(self.calibration_data),
            'calibration_error': calibration_error,
            'avg_raw_confidence': np.mean(confidences),
            'avg_correctness': np.mean(correctness),
            'temperature': self.temperature if self.method == "temperature_scaling" else None
        }
    
    def set_temperature(self, temperature: float):
        """
        Set temperature for temperature scaling method
        
        Args:
            temperature: Temperature parameter (> 1 penalizes overconfidence)
        """
        if temperature <= 0:
            raise ValueError("Temperature must be positive")
        self.temperature = temperature
        if self.method == "temperature_scaling":
            self.is_calibrated = False  # Need to re-evaluate
    
    def evaluate_exclusion_rate(self, threshold: float = 0.4) -> float:
        """
        Evaluate what exclusion rate would be with current calibration
        
        Args:
            threshold: Confidence threshold for exclusion
            
        Returns:
            float: Expected exclusion rate (0-1)
        """
        if not self.calibration_data:
            return 0.0
        
        confidences = np.array([pair[0] for pair in self.calibration_data])
        
        # Apply calibration to all confidences
        calibrated_confidences = np.array([self.calibrate_confidence(conf) for conf in confidences])
        
        # Calculate exclusion rate
        excluded = np.sum(calibrated_confidences < threshold)
        total = len(calibrated_confidences)
        
        return excluded / total if total > 0 else 0.0
