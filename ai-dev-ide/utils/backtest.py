"""
Backtesting Engine
"""
import pandas as pd
import numpy as np
from datetime import datetime

class BacktestEngine:
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.positions = []
        self.trades = []
        self.equity_curve = []
        
    def run_backtest(self, data, strategy):
        """
        Run backtest on data with strategy
        
        Args:
            data: DataFrame with price data
            strategy: Function that returns signals
        """
        capital = self.initial_capital
        position = 0
        equity = capital
        
        for i in range(len(data)):
            current_price = data['close'].iloc[i]
            signal = strategy(data, i)
            
            # Execute trades based on signal
            if signal == 'BUY' and position == 0:
                position = capital / current_price
                capital = 0
                self.trades.append({
                    'timestamp': data.index[i],
                    'type': 'BUY',
                    'price': current_price,
                    'shares': position
                })
            elif signal == 'SELL' and position > 0:
                capital = position * current_price
                self.trades.append({
                    'timestamp': data.index[i],
                    'type': 'SELL',
                    'price': current_price,
                    'shares': position
                })
                position = 0
            
            # Calculate equity
            equity = capital + (position * current_price)
            self.equity_curve.append(equity)
            
            # Record position
            self.positions.append({
                'timestamp': data.index[i],
                'price': current_price,
                'position': position,
                'capital': capital,
                'equity': equity
            })
        
        return pd.DataFrame(self.positions)
    
    def calculate_metrics(self):
        """Calculate performance metrics"""
        if not self.positions:
            return {}
        
        df = pd.DataFrame(self.positions)
        
        # Calculate returns
        df['returns'] = df['equity'].pct_change()
        
        # Total return
        total_return = (df['equity'].iloc[-1] / self.initial_capital) - 1
        
        # Sharpe ratio (assuming risk-free rate = 0)
        if df['returns'].std() > 0:
            sharpe_ratio = (df['returns'].mean() / df['returns'].std()) * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # Maximum drawdown
        df['cummax'] = df['equity'].cummax()
        df['drawdown'] = (df['equity'] - df['cummax']) / df['cummax']
        max_drawdown = df['drawdown'].min()
        
        # Win rate
        if self.trades:
            winning_trades = [t for t in self.trades if t['type'] == 'SELL' and 
                            (t['price'] - self.trades[self.trades.index(t)-1]['price']) > 0]
            win_rate = len(winning_trades) / (len(self.trades) / 2) if self.trades else 0
        else:
            win_rate = 0
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'num_trades': len(self.trades) // 2,
            'final_equity': df['equity'].iloc[-1]
        }