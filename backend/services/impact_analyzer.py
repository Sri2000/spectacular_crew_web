"""
Impact Analyzer
Calculates failure propagation across business functions
"""
import networkx as nx
from typing import Dict, List, Any
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ImpactAnalyzer:
    """Analyzer for failure impact propagation"""
    
    BUSINESS_FUNCTIONS = ['inventory', 'pricing', 'fulfillment', 'revenue']
    
    def __init__(self):
        self.graph = self._build_propagation_graph()
    
    def _build_propagation_graph(self) -> nx.DiGraph:
        """Build network graph for failure propagation"""
        G = nx.DiGraph()
        
        # Add nodes
        for func in self.BUSINESS_FUNCTIONS:
            G.add_node(func)
        
        # Add edges with weights (propagation strength)
        G.add_edge('inventory', 'pricing', weight=0.8)
        G.add_edge('inventory', 'fulfillment', weight=0.9)
        G.add_edge('pricing', 'revenue', weight=0.95)
        G.add_edge('fulfillment', 'revenue', weight=0.85)
        G.add_edge('inventory', 'revenue', weight=0.7)
        
        return G
    
    async def analyze_impact(self, scenario: Dict[str, Any], simulation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze failure impact and calculate propagation score
        
        Args:
            scenario: Failure scenario details
            simulation_result: Simulation results
        
        Returns:
            Propagation score and impact analysis
        """
        try:
            scenario_type = scenario.get('scenario_type')
            
            # Determine initial impact source
            source_function = self._get_source_function(scenario_type)
            
            # Calculate direct impacts
            direct_impacts = self._calculate_direct_impacts(source_function, simulation_result)
            
            # Calculate indirect impacts through propagation
            indirect_impacts = self._calculate_indirect_impacts(source_function, direct_impacts)
            
            # Combine all impacts
            function_impacts = self._combine_impacts(direct_impacts, indirect_impacts)
            
            # Calculate overall propagation score
            overall_score = self._calculate_overall_score(function_impacts)
            
            # Calculate cascade depth
            cascade_depth = self._calculate_cascade_depth(source_function)
            
            # Identify vulnerable functions
            vulnerable_functions = self._identify_vulnerable_functions(function_impacts)
            
            return {
                'id': str(uuid.uuid4()),
                'scenario_id': scenario.get('scenario_id'),
                'overall_score': overall_score,
                'function_impacts': function_impacts,
                'cascade_depth': cascade_depth,
                'affected_business_units': vulnerable_functions,
                'calculation_timestamp': datetime.utcnow(),
                'confidence_metrics': {
                    'direct_impact_confidence': 0.9,
                    'indirect_impact_confidence': 0.75
                }
            }
            
        except Exception as e:
            logger.error(f"Impact analysis error: {str(e)}")
            return None
    
    def _get_source_function(self, scenario_type: str) -> str:
        """Determine source business function based on scenario type"""
        if scenario_type in ['OVERSTOCK', 'STOCKOUT']:
            return 'inventory'
        elif scenario_type == 'PRICING_FAILURE':
            return 'pricing'
        elif scenario_type == 'FULFILLMENT_FAILURE':
            return 'fulfillment'
        else:
            return 'inventory'
    
    def _calculate_direct_impacts(self, source: str, simulation: Dict[str, Any]) -> Dict[str, float]:
        """Calculate direct impacts on source function"""
        impacts = {func: 0.0 for func in self.BUSINESS_FUNCTIONS}
        
        # Calculate source impact based on simulation results
        if 'overstock_costs' in simulation:
            total_cost = sum(simulation['overstock_costs'].values())
            impacts[source] = min(10.0, total_cost / 1000)  # Normalize to 0-10 scale
        elif 'stockout_probabilities' in simulation:
            avg_prob = sum(simulation['stockout_probabilities'].values()) / len(simulation['stockout_probabilities']) if simulation['stockout_probabilities'] else 0
            impacts[source] = avg_prob * 10  # Scale to 0-10
        else:
            impacts[source] = 5.0  # Default moderate impact
        
        return impacts
    
    def _calculate_indirect_impacts(self, source: str, direct_impacts: Dict[str, float]) -> Dict[str, float]:
        """Calculate indirect impacts through network propagation"""
        indirect = {func: 0.0 for func in self.BUSINESS_FUNCTIONS}
        
        source_impact = direct_impacts[source]
        
        # Propagate through network
        for target in self.BUSINESS_FUNCTIONS:
            if target != source and self.graph.has_edge(source, target):
                weight = self.graph[source][target]['weight']
                indirect[target] = source_impact * weight
        
        # Second-order propagation
        for intermediate in self.BUSINESS_FUNCTIONS:
            if indirect[intermediate] > 0:
                for target in self.BUSINESS_FUNCTIONS:
                    if self.graph.has_edge(intermediate, target):
                        weight = self.graph[intermediate][target]['weight']
                        indirect[target] = max(indirect[target], indirect[intermediate] * weight * 0.7)
        
        return indirect
    
    def _combine_impacts(self, direct: Dict[str, float], indirect: Dict[str, float]) -> Dict[str, float]:
        """Combine direct and indirect impacts"""
        combined = {}
        for func in self.BUSINESS_FUNCTIONS:
            combined[func] = round(max(direct[func], indirect[func]), 2)
        return combined
    
    def _calculate_overall_score(self, function_impacts: Dict[str, float]) -> float:
        """Calculate overall propagation score (0-10)"""
        # Weighted average with revenue having highest weight
        weights = {'inventory': 0.2, 'pricing': 0.25, 'fulfillment': 0.2, 'revenue': 0.35}
        score = sum(function_impacts[func] * weights[func] for func in self.BUSINESS_FUNCTIONS)
        return round(score, 2)
    
    def _calculate_cascade_depth(self, source: str) -> int:
        """Calculate maximum cascade depth from source"""
        max_depth = 0
        for target in self.BUSINESS_FUNCTIONS:
            if target != source:
                try:
                    path_length = nx.shortest_path_length(self.graph, source, target)
                    max_depth = max(max_depth, path_length)
                except nx.NetworkXNoPath:
                    pass
        return max_depth
    
    def _identify_vulnerable_functions(self, function_impacts: Dict[str, float]) -> List[str]:
        """Identify most vulnerable business functions"""
        # Sort by impact score
        sorted_functions = sorted(function_impacts.items(), key=lambda x: x[1], reverse=True)
        # Return functions with impact > 5.0
        return [func for func, impact in sorted_functions if impact > 5.0]
