"""
Signal Processing for Learning Analytics
Extracts meaningful signals from user interactions for learning analysis
"""

import numpy as np
from typing import Dict, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SignalExtractor:
    """
    Extracts learning signals from user interactions
    Provides comprehensive analytics for learning behavior analysis
    """
    
    def __init__(self):
        """Initialize signal extractor"""
        self.signal_cache = {}
        logger.info("Signal Extractor initialized")
    
    def extract_learning_signal(self, interaction: Dict[str, any]) -> Dict[str, float]:
        """
        Extract comprehensive learning signals from interaction
        
        Args:
            interaction: User interaction data
            
        Returns:
            Dictionary of extracted signals
        """
        try:
            signals = {}
            
            # Basic performance signals
            signals["correctness_signal"] = 1.0 if interaction.get("correct", False) else 0.0
            signals["response_time_signal"] = self._normalize_response_time(interaction.get("response_time", 0.0))
            signals["difficulty_signal"] = interaction.get("difficulty", 0.5)
            
            # Learning progression signals
            signals["mastery_before_signal"] = interaction.get("mastery_before", 0.5)
            signals["mastery_after_signal"] = interaction.get("mastery_after", 0.5)
            signals["mastery_gain_signal"] = signals["mastery_after_signal"] - signals["mastery_before_signal"]
            
            # Engagement signals
            signals["engagement_signal"] = self._calculate_engagement_signal(interaction)
            signals["consistency_signal"] = self._calculate_consistency_signal(interaction)
            
            # Difficulty adaptation signals
            signals["zpd_alignment_signal"] = self._calculate_zpd_alignment(interaction)
            signals["challenge_appropriateness_signal"] = self._calculate_challenge_appropriateness(interaction)
            
            # Temporal signals
            signals["time_of_day_signal"] = self._calculate_time_of_day_signal(interaction)
            signals["session_progression_signal"] = self._calculate_session_progression_signal(interaction)
            
            # Policy effectiveness signals
            signals["policy_effectiveness_signal"] = self._calculate_policy_effectiveness(interaction)
            
            logger.debug(f"Extracted {len(signals)} signals from interaction")
            return signals
            
        except Exception as e:
            logger.error(f"Error extracting signals: {e}")
            return {}
    
    def _normalize_response_time(self, response_time: float) -> float:
        """Normalize response time to [0, 1] scale"""
        if response_time <= 0:
            return 0.5
        
        # Fast responses = high signal, slow responses = low signal
        if response_time < 5.0:
            return 1.0
        elif response_time < 15.0:
            return 0.8
        elif response_time < 30.0:
            return 0.6
        elif response_time < 60.0:
            return 0.4
        else:
            return 0.2
    
    def _calculate_engagement_signal(self, interaction: Dict[str, any]) -> float:
        """Calculate engagement signal from interaction patterns"""
        # Factors: response time, attempts, hints used
        response_time = interaction.get("response_time", 0.0)
        attempts = interaction.get("attempts", 1)
        hints_used = interaction.get("hints_used", 0)
        
        # Base engagement from response time (moderate time = higher engagement)
        if 5.0 <= response_time <= 30.0:
            time_engagement = 1.0
        elif response_time < 5.0:
            time_engagement = 0.7  # Too fast = low engagement
        else:
            time_engagement = 0.5  # Too slow = low engagement
        
        # Penalty for excessive attempts or hints
        attempt_penalty = min(0.3, (attempts - 1) * 0.1)
        hint_penalty = min(0.2, hints_used * 0.1)
        
        engagement = time_engagement - attempt_penalty - hint_penalty
        return max(0.0, min(1.0, engagement))
    
    def _calculate_consistency_signal(self, interaction: Dict[str, any]) -> float:
        """Calculate consistency signal based on performance patterns"""
        # For now, use correctness as consistency indicator
        # In a full implementation, this would analyze historical patterns
        return 1.0 if interaction.get("correct", False) else 0.0
    
    def _calculate_zpd_alignment(self, interaction: Dict[str, any]) -> float:
        """Calculate Zone of Proximal Development alignment"""
        mastery = interaction.get("mastery_before", 0.5)
        difficulty = interaction.get("difficulty", 0.5)
        
        # ZPD alignment: difficulty should be slightly above mastery
        zpd_difficulty = mastery + 0.1  # Optimal difficulty in ZPD
        alignment = 1.0 - abs(difficulty - zpd_difficulty)
        
        return max(0.0, min(1.0, alignment))
    
    def _calculate_challenge_appropriateness(self, interaction: Dict[str, any]) -> float:
        """Calculate if challenge level is appropriate"""
        mastery = interaction.get("mastery_before", 0.5)
        difficulty = interaction.get("difficulty", 0.5)
        correct = interaction.get("correct", False)
        
        # Challenge is appropriate if:
        # - Correct and difficulty is reasonable for mastery level
        # - Incorrect and difficulty is challenging but not impossible
        
        if correct:
            # For correct answers, difficulty should be <= mastery + 0.2
            appropriate = difficulty <= (mastery + 0.2)
        else:
            # For incorrect answers, difficulty should be > mastery but not too high
            appropriate = mastery < difficulty <= (mastery + 0.3)
        
        return 1.0 if appropriate else 0.0
    
    def _calculate_time_of_day_signal(self, interaction: Dict[str, any]) -> float:
        """Calculate time of day effect on learning"""
        timestamp = interaction.get("timestamp")
        if not timestamp:
            return 0.5
        
        try:
            if isinstance(timestamp, (int, float)):
                dt = datetime.fromtimestamp(timestamp)
            else:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            hour = dt.hour
            
            # Peak learning hours: 9-11 AM and 2-4 PM
            if 9 <= hour <= 11 or 14 <= hour <= 16:
                return 1.0
            elif 8 <= hour <= 12 or 13 <= hour <= 17:
                return 0.8
            elif 19 <= hour <= 21:
                return 0.6
            else:
                return 0.4
                
        except Exception:
            return 0.5
    
    def _calculate_session_progression_signal(self, interaction: Dict[str, any]) -> float:
        """Calculate session progression signal"""
        # This would track position within a learning session
        # For now, return a neutral value
        return 0.5
    
    def _calculate_policy_effectiveness(self, interaction: Dict[str, any]) -> float:
        """Calculate policy effectiveness signal"""
        # Policy effectiveness = learning gain * correctness
        mastery_gain = interaction.get("mastery_after", 0.5) - interaction.get("mastery_before", 0.5)
        correct = 1.0 if interaction.get("correct", False) else 0.0
        
        effectiveness = mastery_gain * correct
        return max(0.0, min(1.0, effectiveness))
    
    def analyze_signal_patterns(self, interactions: List[Dict[str, any]]) -> Dict[str, any]:
        """
        Analyze patterns across multiple interactions
        
        Args:
            interactions: List of user interactions
            
        Returns:
            Pattern analysis results
        """
        if not interactions:
            return {}
        
        try:
            # Extract signals for all interactions
            all_signals = [self.extract_learning_signal(interaction) for interaction in interactions]
            
            # Calculate aggregate statistics
            analysis = {}
            
            for signal_name in all_signals[0].keys():
                signal_values = [signals[signal_name] for signals in all_signals]
                
                analysis[signal_name] = {
                    "mean": np.mean(signal_values),
                    "std": np.std(signal_values),
                    "min": np.min(signal_values),
                    "max": np.max(signal_values),
                    "trend": self._calculate_trend(signal_values)
                }
            
            # Overall learning health indicators
            analysis["learning_health"] = {
                "average_engagement": analysis["engagement_signal"]["mean"],
                "average_mastery_gain": analysis["mastery_gain_signal"]["mean"],
                "zpd_alignment_score": analysis["zpd_alignment_signal"]["mean"],
                "policy_effectiveness": analysis["policy_effectiveness_signal"]["mean"]
            }
            
            logger.info(f"Analyzed signal patterns for {len(interactions)} interactions")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing signal patterns: {e}")
            return {}
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from values"""
        if len(values) < 2:
            return "stable"
        
        # Simple linear regression to determine trend
        x = np.arange(len(values))
        y = np.array(values)
        
        # Calculate slope
        slope = np.polyfit(x, y, 1)[0]
        
        if slope > 0.01:
            return "improving"
        elif slope < -0.01:
            return "declining"
        else:
            return "stable"
    
    def get_learning_insights(self, signal_analysis: Dict[str, any]) -> List[str]:
        """
        Generate learning insights from signal analysis
        
        Args:
            signal_analysis: Results from signal pattern analysis
            
        Returns:
            List of learning insights
        """
        insights = []
        
        try:
            health = signal_analysis.get("learning_health", {})
            
            # Engagement insights
            engagement = health.get("average_engagement", 0.5)
            if engagement < 0.4:
                insights.append("Low engagement detected - consider adjusting difficulty")
            elif engagement > 0.8:
                insights.append("High engagement - current difficulty level is appropriate")
            
            # Mastery gain insights
            mastery_gain = health.get("average_mastery_gain", 0.0)
            if mastery_gain < 0.01:
                insights.append("Low mastery gain - content may be too easy or too hard")
            elif mastery_gain > 0.05:
                insights.append("Strong mastery gain - optimal learning progression")
            
            # ZPD alignment insights
            zpd_alignment = health.get("zpd_alignment_score", 0.5)
            if zpd_alignment < 0.4:
                insights.append("Poor ZPD alignment - adjust difficulty to match skill level")
            elif zpd_alignment > 0.7:
                insights.append("Good ZPD alignment - tasks well-matched to ability")
            
            # Policy effectiveness insights
            policy_effectiveness = health.get("policy_effectiveness", 0.0)
            if policy_effectiveness < 0.3:
                insights.append("Low policy effectiveness - consider policy adjustment")
            elif policy_effectiveness > 0.6:
                insights.append("High policy effectiveness - current strategy working well")
            
            logger.info(f"Generated {len(insights)} learning insights")
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return ["Unable to generate insights due to error"]
