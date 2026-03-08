"""
Seasonal Risk Engine
Analyzes seasonal demand patterns and detects risks
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime
import uuid
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)


class SeasonalRiskEngine:
    """Engine for detecting seasonal demand risks"""
    
    def __init__(self, variance_threshold: float = 0.3):
        self.variance_threshold = variance_threshold
        self.scaler = StandardScaler()
    
    async def analyze_seasonal_risks(self, market_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze seasonal demand patterns and detect risks
        
        Args:
            market_data: List of market trend records
        
        Returns:
            List of risk assessments
        """
        try:
            # Convert to DataFrame
            df = pd.DataFrame(market_data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            risk_assessments = []
            
            # Group by product category
            for category in df['product_category'].unique():
                category_data = df[df['product_category'] == category]
                
                # Calculate risk metrics
                risk_assessment = self._calculate_category_risk(category, category_data)
                
                if risk_assessment:
                    risk_assessments.append(risk_assessment)
            
            # Prioritize by revenue impact if available
            risk_assessments = self._prioritize_by_revenue(risk_assessments)
            
            return risk_assessments
            
        except Exception as e:
            logger.error(f"Seasonal risk analysis error: {str(e)}")
            return []
    
    def _calculate_category_risk(self, category: str, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate risk metrics for a product category"""
        try:
            # Calculate moving average
            data['ma_7'] = data['demand_forecast'].rolling(window=7, min_periods=1).mean()
            data['ma_30'] = data['demand_forecast'].rolling(window=30, min_periods=1).mean()
            
            # Calculate variance
            variance = data['demand_forecast'].std() / data['demand_forecast'].mean() if data['demand_forecast'].mean() > 0 else 0
            
            # Detect seasonal mismatch
            recent_demand = data['demand_forecast'].tail(7).mean()
            historical_demand = data['demand_forecast'].mean()
            demand_change = abs(recent_demand - historical_demand) / historical_demand if historical_demand > 0 else 0
            
            # Calculate risk score
            risk_score = min(1.0, (variance + demand_change) / 2)
            
            # Determine risk type
            risk_type = "SEASONAL_MISMATCH"
            if recent_demand > historical_demand * 1.2:
                risk_type = "STOCKOUT"
            elif recent_demand < historical_demand * 0.8:
                risk_type = "OVERSTOCK"
            
            # Flag if exceeds threshold
            is_flagged = variance > self.variance_threshold or demand_change > self.variance_threshold
            
            if not is_flagged:
                return None
            
            return {
                'id': str(uuid.uuid4()),
                'product_category': category,
                'risk_score': round(risk_score, 3),
                'risk_type': risk_type,
                'confidence_level': round(1 - variance, 3),
                'detection_timestamp': datetime.utcnow(),
                'contributing_factors': [
                    f"Variance: {round(variance, 3)}",
                    f"Demand change: {round(demand_change * 100, 1)}%"
                ],
                'historical_comparison': {
                    'recent_demand': round(recent_demand, 2),
                    'historical_demand': round(historical_demand, 2),
                    'variance': round(variance, 3)
                }
            }
            
        except Exception as e:
            logger.error(f"Category risk calculation error for {category}: {str(e)}")
            return None
    
    def _prioritize_by_revenue(self, risk_assessments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize risks by revenue impact (using risk score as proxy)"""
        return sorted(risk_assessments, key=lambda x: x['risk_score'], reverse=True)
