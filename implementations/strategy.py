from typing import Dict, Any, Optional, List
import numpy as np
from datetime import datetime, timedelta
from interfaces.strategy_interface import StrategyInterface

class StrategyImplementation(StrategyInterface):
    """Імплементація для торгової стратегії на Solana"""

    def __init__(self):
        """Ініціалізація стратегії"""
        self.config = {}
        self.market_data_history = []
        self.max_history_size = 1000
        self.min_price_change = 0.02  # 2%
        self.min_volume_change = 0.5   # 50%
        self.rsi_period = 14
        self.rsi_overbought = 70
        self.rsi_oversold = 30

    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Ініціалізація стратегії"""
        try:
            # Зберігаємо конфігурацію
            self.config = config
            
            # Налаштовуємо параметри з конфігурації
            self.min_price_change = config.get('min_price_change', 0.02)
            self.min_volume_change = config.get('min_volume_change', 0.5)
            self.rsi_period = config.get('rsi_period', 14)
            self.rsi_overbought = config.get('rsi_overbought', 70)
            self.rsi_oversold = config.get('rsi_oversold', 30)
            self.max_history_size = config.get('max_history_size', 1000)
            
            return True
            
        except Exception as e:
            print(f"Error initializing strategy: {e}")
            return False

    async def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Аналіз ринкових даних"""
        try:
            # Додаємо нові дані в історію
            self.market_data_history.append(market_data)
            
            # Обмежуємо розмір історії
            if len(self.market_data_history) > self.max_history_size:
                self.market_data_history = self.market_data_history[-self.max_history_size:]
            
            # Отримуємо необхідні дані
            current_price = float(market_data['price'])
            current_volume = float(market_data['volume'])
            
            # Розраховуємо технічні індикатори
            rsi = self._calculate_rsi()
            price_change = self._calculate_price_change()
            volume_change = self._calculate_volume_change()
            
            # Формуємо результат аналізу
            analysis = {
                'timestamp': datetime.now().isoformat(),
                'price': current_price,
                'volume': current_volume,
                'rsi': rsi,
                'price_change': price_change,
                'volume_change': volume_change,
                'indicators': {
                    'rsi_overbought': rsi > self.rsi_overbought,
                    'rsi_oversold': rsi < self.rsi_oversold,
                    'significant_price_change': abs(price_change) > self.min_price_change,
                    'significant_volume_change': volume_change > self.min_volume_change
                }
            }
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing market data: {e}")
            return {}

    async def generate_signal(self, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Генерація торгового сигналу"""
        try:
            if not analysis:
                return None
                
            indicators = analysis.get('indicators', {})
            
            # Перевіряємо умови для сигналу на покупку
            if (indicators.get('rsi_oversold', False) and
                indicators.get('significant_volume_change', False)):
                return {
                    'action': 'buy',
                    'token': analysis.get('token'),
                    'price': analysis.get('price'),
                    'timestamp': datetime.now().isoformat(),
                    'reason': 'RSI oversold with high volume',
                    'confidence': self._calculate_confidence(analysis)
                }
                
            # Перевіряємо умови для сигналу на продаж
            if (indicators.get('rsi_overbought', False) and
                indicators.get('significant_price_change', False)):
                return {
                    'action': 'sell',
                    'token': analysis.get('token'),
                    'price': analysis.get('price'),
                    'timestamp': datetime.now().isoformat(),
                    'reason': 'RSI overbought with significant price change',
                    'confidence': self._calculate_confidence(analysis)
                }
                
            return None
            
        except Exception as e:
            print(f"Error generating signal: {e}")
            return None

    async def validate_signal(self, signal: Dict[str, Any]) -> bool:
        """Валідація торгового сигналу"""
        try:
            if not signal:
                return False
                
            required_fields = ['action', 'token', 'price', 'timestamp']
            if not all(field in signal for field in required_fields):
                return False
                
            # Перевіряємо час сигналу
            signal_time = datetime.fromisoformat(signal['timestamp'])
            if datetime.now() - signal_time > timedelta(minutes=5):
                return False
                
            # Перевіряємо впевненість сигналу
            if signal.get('confidence', 0) < 0.7:  # Мінімальна впевненість 70%
                return False
                
            return True
            
        except Exception as e:
            print(f"Error validating signal: {e}")
            return False

    def _calculate_rsi(self) -> float:
        """Розрахунок RSI"""
        try:
            if len(self.market_data_history) < self.rsi_period + 1:
                return 50.0
                
            prices = [float(data['price']) for data in self.market_data_history]
            deltas = np.diff(prices)
            
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains[-self.rsi_period:])
            avg_loss = np.mean(losses[-self.rsi_period:])
            
            if avg_loss == 0:
                return 100.0
                
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi)
            
        except Exception as e:
            print(f"Error calculating RSI: {e}")
            return 50.0

    def _calculate_price_change(self) -> float:
        """Розрахунок зміни ціни"""
        try:
            if len(self.market_data_history) < 2:
                return 0.0
                
            current_price = float(self.market_data_history[-1]['price'])
            previous_price = float(self.market_data_history[-2]['price'])
            
            return (current_price - previous_price) / previous_price
            
        except Exception as e:
            print(f"Error calculating price change: {e}")
            return 0.0

    def _calculate_volume_change(self) -> float:
        """Розрахунок зміни об'єму"""
        try:
            if len(self.market_data_history) < 2:
                return 0.0
                
            current_volume = float(self.market_data_history[-1]['volume'])
            previous_volume = float(self.market_data_history[-2]['volume'])
            
            return (current_volume - previous_volume) / previous_volume
            
        except Exception as e:
            print(f"Error calculating volume change: {e}")
            return 0.0

    def _calculate_confidence(self, analysis: Dict[str, Any]) -> float:
        """Розрахунок впевненості сигналу"""
        try:
            confidence = 0.0
            indicators = analysis.get('indicators', {})
            
            # Додаємо вагу кожного індикатора
            if indicators.get('rsi_overbought') or indicators.get('rsi_oversold'):
                confidence += 0.4
                
            if indicators.get('significant_price_change'):
                confidence += 0.3
                
            if indicators.get('significant_volume_change'):
                confidence += 0.3
                
            return min(confidence, 1.0)
            
        except Exception as e:
            print(f"Error calculating confidence: {e}")
            return 0.0 