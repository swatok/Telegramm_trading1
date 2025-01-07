"""Market calculator utilities"""

from decimal import Decimal
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class MarketCalculator:
    """Клас для розрахунку ринкових метрик"""
    
    @staticmethod
    def calculate_price_change(
        start_price: Decimal,
        end_price: Decimal
    ) -> Decimal:
        """Розрахунок зміни ціни у відсотках"""
        if start_price == 0:
            return Decimal('0')
            
        return ((end_price - start_price) / start_price) * Decimal('100')
    
    @staticmethod
    def calculate_volatility(prices: List[Decimal]) -> Decimal:
        """Розрахунок волатильності"""
        if len(prices) < 2:
            return Decimal('0')
            
        # Розрахунок прибутковості
        returns = [
            (prices[i] - prices[i-1]) / prices[i-1]
            for i in range(1, len(prices))
        ]
        
        # Розрахунок середнього значення
        mean = sum(returns) / Decimal(len(returns))
        
        # Розрахунок дисперсії
        variance = sum((r - mean) ** 2 for r in returns) / Decimal(len(returns))
        
        # Розрахунок стандартного відхилення (волатильності)
        return variance.sqrt() * Decimal('100')
    
    @staticmethod
    def calculate_moving_average(
        prices: List[Decimal],
        period: int
    ) -> List[Decimal]:
        """Розрахунок ковзної середньої"""
        if len(prices) < period:
            return []
            
        ma = []
        for i in range(period - 1, len(prices)):
            window = prices[i - period + 1:i + 1]
            ma.append(sum(window) / Decimal(period))
            
        return ma
    
    @staticmethod
    def calculate_exponential_ma(
        prices: List[Decimal],
        period: int,
        smoothing: Decimal = Decimal('2')
    ) -> List[Decimal]:
        """Розрахунок експоненціальної ковзної середньої"""
        if len(prices) < period:
            return []
            
        ema = [sum(prices[:period]) / Decimal(period)]
        multiplier = smoothing / (Decimal(period) + Decimal('1'))
        
        for price in prices[period:]:
            ema.append(
                (price * multiplier) + 
                (ema[-1] * (Decimal('1') - multiplier))
            )
            
        return ema
    
    @staticmethod
    def calculate_rsi(
        prices: List[Decimal],
        period: int = 14
    ) -> Optional[Decimal]:
        """Розрахунок індексу відносної сили (RSI)"""
        if len(prices) < period + 1:
            return None
            
        # Розрахунок змін цін
        changes = [
            prices[i] - prices[i-1]
            for i in range(1, len(prices))
        ]
        
        # Розділення на позитивні та негативні зміни
        gains = [max(change, Decimal('0')) for change in changes]
        losses = [abs(min(change, Decimal('0'))) for change in changes]
        
        # Розрахунок середніх значень
        avg_gain = sum(gains[:period]) / Decimal(period)
        avg_loss = sum(losses[:period]) / Decimal(period)
        
        if avg_loss == 0:
            return Decimal('100')
            
        rs = avg_gain / avg_loss
        return Decimal('100') - (Decimal('100') / (Decimal('1') + rs))
    
    @staticmethod
    def calculate_bollinger_bands(
        prices: List[Decimal],
        period: int = 20,
        std_dev: Decimal = Decimal('2')
    ) -> Dict[str, List[Decimal]]:
        """Розрахунок смуг Боллінджера"""
        if len(prices) < period:
            return {'upper': [], 'middle': [], 'lower': []}
            
        # Розрахунок середньої лінії (SMA)
        middle = MarketCalculator.calculate_moving_average(prices, period)
        
        upper = []
        lower = []
        
        for i in range(len(middle)):
            # Розрахунок стандартного відхилення
            window = prices[i:i + period]
            mean = sum(window) / Decimal(period)
            variance = sum((p - mean) ** 2 for p in window) / Decimal(period)
            std = variance.sqrt()
            
            # Розрахунок верхньої та нижньої смуг
            upper.append(middle[i] + (std * std_dev))
            lower.append(middle[i] - (std * std_dev))
            
        return {
            'upper': upper,
            'middle': middle,
            'lower': lower
        }
    
    @staticmethod
    def calculate_macd(
        prices: List[Decimal],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Dict[str, List[Decimal]]:
        """Розрахунок MACD"""
        if len(prices) < slow_period:
            return {'macd': [], 'signal': [], 'histogram': []}
            
        # Розрахунок швидкої та повільної EMA
        fast_ema = MarketCalculator.calculate_exponential_ma(prices, fast_period)
        slow_ema = MarketCalculator.calculate_exponential_ma(prices, slow_period)
        
        # Розрахунок лінії MACD
        macd = [
            fast - slow
            for fast, slow in zip(fast_ema[slow_period-fast_period:], slow_ema)
        ]
        
        # Розрахунок сигнальної лінії
        signal = MarketCalculator.calculate_exponential_ma(macd, signal_period)
        
        # Розрахунок гістограми
        histogram = [
            macd_val - signal_val
            for macd_val, signal_val in zip(macd[signal_period-1:], signal)
        ]
        
        return {
            'macd': macd[signal_period-1:],
            'signal': signal,
            'histogram': histogram
        }
    
    @staticmethod
    def calculate_atr(
        high_prices: List[Decimal],
        low_prices: List[Decimal],
        close_prices: List[Decimal],
        period: int = 14
    ) -> Optional[Decimal]:
        """Розрахунок середнього істинного діапазону (ATR)"""
        if len(high_prices) < period or \
           len(low_prices) < period or \
           len(close_prices) < period:
            return None
            
        # Розрахунок істинних діапазонів
        tr = []
        for i in range(1, len(close_prices)):
            high = high_prices[i]
            low = low_prices[i]
            prev_close = close_prices[i-1]
            
            tr.append(max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            ))
            
        # Розрахунок ATR
        if not tr:
            return None
            
        return sum(tr[-period:]) / Decimal(period)
    
    @staticmethod
    def calculate_support_resistance(
        prices: List[Decimal],
        window_size: int = 20,
        threshold: Decimal = Decimal('0.02')
    ) -> Dict[str, List[Decimal]]:
        """Розрахунок рівнів підтримки та опору"""
        if len(prices) < window_size:
            return {'support': [], 'resistance': []}
            
        support = []
        resistance = []
        
        for i in range(window_size, len(prices) - window_size):
            current_price = prices[i]
            left_window = prices[i - window_size:i]
            right_window = prices[i + 1:i + window_size + 1]
            
            # Перевірка на мінімум (підтримка)
            if current_price == min(left_window + [current_price] + right_window):
                support.append(current_price)
                
            # Перевірка на максимум (опір)
            if current_price == max(left_window + [current_price] + right_window):
                resistance.append(current_price)
                
        # Фільтрація близьких рівнів
        filtered_support = []
        filtered_resistance = []
        
        for level in support:
            if not filtered_support or \
               all(abs(level - s) / s > threshold for s in filtered_support):
                filtered_support.append(level)
                
        for level in resistance:
            if not filtered_resistance or \
               all(abs(level - r) / r > threshold for r in filtered_resistance):
                filtered_resistance.append(level)
                
        return {
            'support': sorted(filtered_support),
            'resistance': sorted(filtered_resistance)
        } 