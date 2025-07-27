"""
Gold Digger AI Bot - Strategy Optimizer
Parameter optimization and strategy enhancement
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from itertools import product
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

from .backtester import BacktestEngine

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StrategyOptimizer:
    """
    Advanced strategy optimization for SMC parameters
    Tests different parameter combinations to find optimal settings
    """
    
    def __init__(self):
        """Initialize strategy optimizer"""
        self.optimization_results = []
        self.best_parameters = None
        self.best_performance = None
        
        logger.info("StrategyOptimizer initialized")
    
    def optimize_parameters(self, market_data: pd.DataFrame, 
                          optimization_period: Tuple[str, str],
                          validation_period: Tuple[str, str]) -> Dict[str, any]:
        """
        Optimize strategy parameters using walk-forward analysis
        
        Args:
            market_data: Historical market data
            optimization_period: (start_date, end_date) for optimization
            validation_period: (start_date, end_date) for validation
            
        Returns:
            Optimization results with best parameters
        """
        try:
            logger.info("Starting parameter optimization...")
            
            # Define parameter ranges for optimization
            parameter_ranges = self._get_parameter_ranges()
            
            # Generate parameter combinations
            param_combinations = self._generate_parameter_combinations(parameter_ranges)
            
            logger.info(f"Testing {len(param_combinations)} parameter combinations")
            
            # Run optimization
            optimization_results = self._run_optimization(
                market_data, param_combinations, optimization_period
            )
            
            # Find best parameters
            best_params = self._select_best_parameters(optimization_results)
            
            # Validate on out-of-sample data
            validation_results = self._validate_parameters(
                market_data, best_params, validation_period
            )
            
            # Compile final results
            results = {
                'optimization_period': optimization_period,
                'validation_period': validation_period,
                'total_combinations_tested': len(param_combinations),
                'best_parameters': best_params,
                'optimization_performance': optimization_results[0] if optimization_results else None,
                'validation_performance': validation_results,
                'parameter_sensitivity': self._analyze_parameter_sensitivity(optimization_results),
                'recommendations': self._generate_recommendations(best_params, validation_results)
            }
            
            logger.info("Parameter optimization completed")
            return results
            
        except Exception as e:
            logger.error(f"Optimization error: {str(e)}")
            return {'error': str(e)}
    
    def _get_parameter_ranges(self) -> Dict[str, List]:
        """Define parameter ranges for optimization"""
        return {
            'risk_per_trade': [0.005, 0.01, 0.015, 0.02],  # 0.5% to 2%
            'min_confidence': [0.6, 0.7, 0.75, 0.8, 0.85],  # AI confidence threshold
            'min_setup_quality': [5, 6, 7, 8],  # SMC setup quality threshold
            'risk_reward_ratio': [1.5, 2.0, 2.5, 3.0],  # Minimum R:R ratio
            'max_daily_trades': [3, 5, 7, 10],  # Daily trade limit
            'stop_loss_pips': [3, 5, 7, 10],  # Stop loss distance from OB
            'session_filter': ['ALL', 'LONDON_NY', 'NY_ONLY']  # Trading session filter
        }
    
    def _generate_parameter_combinations(self, parameter_ranges: Dict[str, List]) -> List[Dict]:
        """Generate all parameter combinations"""
        keys = list(parameter_ranges.keys())
        values = list(parameter_ranges.values())
        
        combinations = []
        for combination in product(*values):
            param_dict = dict(zip(keys, combination))
            combinations.append(param_dict)
        
        # Limit combinations for practical testing (top 100)
        if len(combinations) > 100:
            # Sample combinations focusing on key parameters
            np.random.seed(42)
            selected_indices = np.random.choice(len(combinations), 100, replace=False)
            combinations = [combinations[i] for i in selected_indices]
        
        return combinations
    
    def _run_optimization(self, market_data: pd.DataFrame, 
                         param_combinations: List[Dict], 
                         period: Tuple[str, str]) -> List[Dict]:
        """Run backtests for all parameter combinations"""
        results = []
        
        for i, params in enumerate(param_combinations):
            try:
                # Create backtester with custom parameters
                backtester = BacktestEngine()
                
                # Apply parameters (simplified for demo)
                backtester.risk_per_trade = params['risk_per_trade']
                backtester.max_daily_trades = params['max_daily_trades']
                
                # Run backtest
                backtest_result = backtester.run_backtest(market_data, period[0], period[1])
                
                # Add parameters to result
                backtest_result['parameters'] = params
                backtest_result['optimization_score'] = self._calculate_optimization_score(backtest_result)
                
                results.append(backtest_result)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Completed {i + 1}/{len(param_combinations)} optimizations")
                    
            except Exception as e:
                logger.error(f"Error in optimization {i}: {str(e)}")
                continue
        
        # Sort by optimization score
        results.sort(key=lambda x: x.get('optimization_score', 0), reverse=True)
        return results
    
    def _calculate_optimization_score(self, backtest_result: Dict) -> float:
        """
        Calculate optimization score combining multiple metrics
        
        Args:
            backtest_result: Backtest results
            
        Returns:
            Optimization score (higher is better)
        """
        try:
            # Extract key metrics
            win_rate = backtest_result.get('win_rate', 0) / 100  # Convert to decimal
            total_return = backtest_result.get('total_return', 0) / 100
            max_drawdown = backtest_result.get('max_drawdown', 100) / 100
            profit_factor = backtest_result.get('profit_factor', 0)
            total_trades = backtest_result.get('total_trades', 0)
            
            # Weighted scoring system
            score = 0
            
            # Win rate component (25% weight)
            if win_rate >= 0.67:  # Target win rate
                score += 25 * (win_rate / 0.67)
            else:
                score += 25 * (win_rate / 0.67) * 0.5  # Penalty for low win rate
            
            # Return component (30% weight)
            if total_return > 0:
                score += 30 * min(2.0, total_return / 0.02)  # Cap at 2% monthly return
            
            # Drawdown component (25% weight) - lower is better
            if max_drawdown <= 0.10:  # Target max 10% drawdown
                score += 25 * (1 - max_drawdown / 0.10)
            
            # Profit factor component (15% weight)
            if profit_factor >= 1.5:
                score += 15 * min(2.0, profit_factor / 1.5)
            
            # Trade frequency component (5% weight)
            if total_trades >= 10:
                score += 5 * min(2.0, total_trades / 20)
            
            return max(0, score)
            
        except Exception as e:
            logger.error(f"Error calculating optimization score: {str(e)}")
            return 0
    
    def _select_best_parameters(self, optimization_results: List[Dict]) -> Dict:
        """Select best parameters from optimization results"""
        if not optimization_results:
            return {}
        
        # Return parameters from best performing combination
        best_result = optimization_results[0]
        return best_result.get('parameters', {})
    
    def _validate_parameters(self, market_data: pd.DataFrame, 
                           best_params: Dict, 
                           validation_period: Tuple[str, str]) -> Dict:
        """Validate best parameters on out-of-sample data"""
        try:
            # Create backtester with best parameters
            backtester = BacktestEngine()
            backtester.risk_per_trade = best_params.get('risk_per_trade', 0.01)
            backtester.max_daily_trades = best_params.get('max_daily_trades', 5)
            
            # Run validation backtest
            validation_result = backtester.run_backtest(
                market_data, validation_period[0], validation_period[1]
            )
            
            validation_result['validation_score'] = self._calculate_optimization_score(validation_result)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_parameter_sensitivity(self, optimization_results: List[Dict]) -> Dict[str, any]:
        """Analyze sensitivity of performance to parameter changes"""
        try:
            if len(optimization_results) < 10:
                return {'error': 'Insufficient data for sensitivity analysis'}
            
            # Extract parameter values and scores
            param_data = {}
            for result in optimization_results:
                params = result.get('parameters', {})
                score = result.get('optimization_score', 0)
                
                for param_name, param_value in params.items():
                    if param_name not in param_data:
                        param_data[param_name] = {'values': [], 'scores': []}
                    param_data[param_name]['values'].append(param_value)
                    param_data[param_name]['scores'].append(score)
            
            # Calculate correlations
            sensitivity_analysis = {}
            for param_name, data in param_data.items():
                if len(set(data['values'])) > 1:  # Only if parameter varies
                    correlation = np.corrcoef(data['values'], data['scores'])[0, 1]
                    sensitivity_analysis[param_name] = {
                        'correlation': round(correlation, 3),
                        'sensitivity': 'HIGH' if abs(correlation) > 0.5 else 'MEDIUM' if abs(correlation) > 0.3 else 'LOW',
                        'optimal_range': self._find_optimal_range(data['values'], data['scores'])
                    }
            
            return sensitivity_analysis
            
        except Exception as e:
            logger.error(f"Sensitivity analysis error: {str(e)}")
            return {'error': str(e)}
    
    def _find_optimal_range(self, values: List, scores: List) -> Dict:
        """Find optimal parameter range"""
        try:
            # Find top 25% performing values
            combined = list(zip(values, scores))
            combined.sort(key=lambda x: x[1], reverse=True)
            
            top_25_percent = combined[:max(1, len(combined) // 4)]
            top_values = [x[0] for x in top_25_percent]
            
            return {
                'min': min(top_values),
                'max': max(top_values),
                'mean': np.mean(top_values),
                'recommended': np.median(top_values)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _generate_recommendations(self, best_params: Dict, validation_results: Dict) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        try:
            # Check validation performance
            validation_score = validation_results.get('validation_score', 0)
            win_rate = validation_results.get('win_rate', 0)
            max_drawdown = validation_results.get('max_drawdown', 0)
            
            if validation_score >= 70:
                recommendations.append("✅ Strategy parameters are well-optimized and validated")
            elif validation_score >= 50:
                recommendations.append("⚠️ Strategy shows promise but may need further refinement")
            else:
                recommendations.append("❌ Strategy requires significant optimization")
            
            # Specific parameter recommendations
            if best_params.get('risk_per_trade', 0) > 0.015:
                recommendations.append("💡 Consider reducing risk per trade for better drawdown control")
            
            if win_rate < 60:
                recommendations.append("💡 Focus on improving setup quality filters to increase win rate")
            
            if max_drawdown > 15:
                recommendations.append("💡 Implement stricter risk management to reduce drawdown")
            
            # Session recommendations
            session_filter = best_params.get('session_filter', 'ALL')
            if session_filter != 'ALL':
                recommendations.append(f"💡 Optimal trading during {session_filter} sessions")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return ["❌ Unable to generate recommendations due to error"]
    
    def generate_optimization_report(self, optimization_results: Dict) -> str:
        """Generate comprehensive optimization report"""
        try:
            report = f"""
# 🏆 Gold Digger AI Bot - Strategy Optimization Report

## 📊 Optimization Summary
- **Period**: {optimization_results.get('optimization_period', 'N/A')}
- **Validation Period**: {optimization_results.get('validation_period', 'N/A')}
- **Combinations Tested**: {optimization_results.get('total_combinations_tested', 0)}

## 🎯 Best Parameters
"""
            
            best_params = optimization_results.get('best_parameters', {})
            for param, value in best_params.items():
                report += f"- **{param}**: {value}\n"
            
            report += f"""
## 📈 Performance Results

### Optimization Period
"""
            opt_perf = optimization_results.get('optimization_performance', {})
            if opt_perf:
                report += f"""
- **Win Rate**: {opt_perf.get('win_rate', 0):.1f}%
- **Total Return**: {opt_perf.get('total_return', 0):.2f}%
- **Max Drawdown**: {opt_perf.get('max_drawdown', 0):.2f}%
- **Profit Factor**: {opt_perf.get('profit_factor', 0):.2f}
- **Total Trades**: {opt_perf.get('total_trades', 0)}
"""
            
            report += f"""
### Validation Period
"""
            val_perf = optimization_results.get('validation_performance', {})
            if val_perf:
                report += f"""
- **Win Rate**: {val_perf.get('win_rate', 0):.1f}%
- **Total Return**: {val_perf.get('total_return', 0):.2f}%
- **Max Drawdown**: {val_perf.get('max_drawdown', 0):.2f}%
- **Profit Factor**: {val_perf.get('profit_factor', 0):.2f}
- **Total Trades**: {val_perf.get('total_trades', 0)}
"""
            
            report += f"""
## 💡 Recommendations
"""
            recommendations = optimization_results.get('recommendations', [])
            for rec in recommendations:
                report += f"- {rec}\n"
            
            return report
            
        except Exception as e:
            return f"Error generating report: {str(e)}"

# Test function
def test_optimizer():
    """Test strategy optimizer"""
    print("🔍 Testing Strategy Optimizer...")
    
    # Create sample data
    dates = pd.date_range(start='2024-01-01', end='2024-03-31', freq='5min')
    np.random.seed(42)
    
    data = []
    base_price = 1987.0
    for date in dates:
        price = base_price + np.random.normal(0, 2)
        data.append({
            'Open': price,
            'High': price + abs(np.random.normal(0, 1)),
            'Low': price - abs(np.random.normal(0, 1)),
            'Close': price + np.random.normal(0, 0.5),
            'Volume': np.random.randint(100, 1000)
        })
        base_price = data[-1]['Close']
    
    df = pd.DataFrame(data, index=dates)
    
    # Test optimizer
    optimizer = StrategyOptimizer()
    results = optimizer.optimize_parameters(
        df, 
        ('2024-01-01', '2024-02-29'),  # Optimization period
        ('2024-03-01', '2024-03-31')   # Validation period
    )
    
    print("✅ Strategy Optimizer Test Results:")
    print(f"   Combinations Tested: {results.get('total_combinations_tested', 0)}")
    print(f"   Best Risk per Trade: {results.get('best_parameters', {}).get('risk_per_trade', 'N/A')}")
    print(f"   Validation Score: {results.get('validation_performance', {}).get('validation_score', 0):.1f}")
    
    # Generate report
    report = optimizer.generate_optimization_report(results)
    print(f"   Report Generated: {len(report)} characters")
    
    return True

if __name__ == "__main__":
    test_optimizer()
