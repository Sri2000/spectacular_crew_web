"""
Retail Failure Simulator
Models inventory overstock and stockout scenarios
"""
import numpy as np
from typing import Dict, List, Any
from datetime import datetime, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)


class RetailFailureSimulator:
    """Simulator for retail failure scenarios"""
    
    def __init__(self):
        self.simulation_id = None
    
    async def simulate_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate a failure scenario
        
        Args:
            scenario: Scenario configuration with type, products, time horizon, parameters
        
        Returns:
            Simulation results with inventory levels, probabilities, costs
        """
        self.simulation_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        try:
            scenario_type = scenario.get('scenario_type')
            time_horizon = scenario.get('time_horizon', 30)
            affected_products = scenario.get('affected_products', [])
            initial_conditions = scenario.get('initial_conditions', {})
            parameters = scenario.get('simulation_parameters', {})
            
            # Run simulation based on type
            if scenario_type == 'OVERSTOCK':
                results = self._simulate_overstock(time_horizon, affected_products, initial_conditions, parameters)
            elif scenario_type == 'STOCKOUT':
                results = self._simulate_stockout(time_horizon, affected_products, initial_conditions, parameters)
            else:
                results = self._simulate_generic(time_horizon, affected_products, initial_conditions, parameters)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                'result_id': str(uuid.uuid4()),
                'scenario_id': scenario.get('scenario_id', self.simulation_id),
                'simulation_data': results['time_series'],
                'inventory_levels': results['inventory_levels'],
                'stockout_probabilities': results['stockout_probabilities'],
                'overstock_costs': results['overstock_costs'],
                'execution_time_seconds': execution_time,
                'simulation_timestamp': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Simulation error: {str(e)}")
            return None
    
    def _simulate_overstock(self, days: int, products: List[str], initial: Dict, params: Dict) -> Dict[str, Any]:
        """Simulate overstock scenario"""
        base_inventory = initial.get('base_inventory', 1000)
        demand_rate = params.get('demand_rate', 50)
        overstock_factor = params.get('overstock_factor', 2.0)
        
        time_series = []
        inventory_levels = {}
        overstock_costs = {}
        
        for product in products:
            inventory = base_inventory * overstock_factor
            product_series = []
            daily_costs = []
            
            for day in range(days):
                # Simulate daily demand with randomness
                daily_demand = max(0, np.random.normal(demand_rate, demand_rate * 0.2))
                inventory = max(0, inventory - daily_demand)
                
                # Calculate overstock cost
                overstock_amount = max(0, inventory - base_inventory)
                holding_cost = overstock_amount * 0.01  # $0.01 per unit per day
                
                product_series.append({
                    'day': day,
                    'inventory': round(inventory, 2),
                    'demand': round(daily_demand, 2),
                    'overstock': round(overstock_amount, 2)
                })
                daily_costs.append(round(holding_cost, 2))
            
            time_series.append({'product': product, 'data': product_series})
            inventory_levels[product] = [d['inventory'] for d in product_series]
            overstock_costs[product] = sum(daily_costs)
        
        return {
            'time_series': time_series,
            'inventory_levels': inventory_levels,
            'stockout_probabilities': {p: 0.0 for p in products},
            'overstock_costs': overstock_costs
        }
    
    def _simulate_stockout(self, days: int, products: List[str], initial: Dict, params: Dict) -> Dict[str, Any]:
        """Simulate stockout scenario"""
        base_inventory = initial.get('base_inventory', 1000)
        demand_rate = params.get('demand_rate', 50)
        stockout_factor = params.get('stockout_factor', 0.5)
        
        time_series = []
        inventory_levels = {}
        stockout_probs = {}
        
        for product in products:
            inventory = base_inventory * stockout_factor
            product_series = []
            stockout_days = 0
            
            for day in range(days):
                daily_demand = max(0, np.random.normal(demand_rate, demand_rate * 0.2))
                
                if inventory < daily_demand:
                    stockout_days += 1
                
                inventory = max(0, inventory - daily_demand)
                
                product_series.append({
                    'day': day,
                    'inventory': round(inventory, 2),
                    'demand': round(daily_demand, 2),
                    'stockout': inventory == 0
                })
            
            time_series.append({'product': product, 'data': product_series})
            inventory_levels[product] = [d['inventory'] for d in product_series]
            stockout_probs[product] = round(stockout_days / days, 3)
        
        return {
            'time_series': time_series,
            'inventory_levels': inventory_levels,
            'stockout_probabilities': stockout_probs,
            'overstock_costs': {p: 0.0 for p in products}
        }
    
    def _simulate_generic(self, days: int, products: List[str], initial: Dict, params: Dict) -> Dict[str, Any]:
        """Generic simulation for other scenario types"""
        base_inventory = initial.get('base_inventory', 1000)
        demand_rate = params.get('demand_rate', 50)
        
        time_series = []
        inventory_levels = {}
        
        for product in products:
            inventory = base_inventory
            product_series = []
            
            for day in range(days):
                daily_demand = max(0, np.random.normal(demand_rate, demand_rate * 0.3))
                inventory = max(0, inventory - daily_demand)
                
                product_series.append({
                    'day': day,
                    'inventory': round(inventory, 2),
                    'demand': round(daily_demand, 2)
                })
            
            time_series.append({'product': product, 'data': product_series})
            inventory_levels[product] = [d['inventory'] for d in product_series]
        
        return {
            'time_series': time_series,
            'inventory_levels': inventory_levels,
            'stockout_probabilities': {p: 0.0 for p in products},
            'overstock_costs': {p: 0.0 for p in products}
        }
