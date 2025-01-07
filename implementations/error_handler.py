from typing import Dict, Any, Optional, Callable
import traceback
import logging
from datetime import datetime
from interfaces.error_handler_interface import ErrorHandlerInterface

class ErrorHandlerImplementation(ErrorHandlerInterface):
    """Імплементація для обробки помилок"""
    
    def __init__(self):
        """Ініціалізація обробника помилок"""
        self.logger = logging.getLogger('error_handler')
        self.notification_callback = None
        self.error_handlers = {}
        self.retry_attempts = 3
        
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Ініціалізація обробника"""
        try:
            # Налаштовуємо логування
            log_level = getattr(logging, config.get('log_level', 'INFO'))
            self.logger.setLevel(log_level)
            
            # Налаштовуємо кількість спроб повтору
            self.retry_attempts = config.get('retry_attempts', 3)
            
            # Реєструємо обробники для різних типів помилок
            self._register_error_handlers()
            
            return True
            
        except Exception as e:
            print(f"Error initializing error handler: {e}")
            return False
            
    async def handle_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Обробка помилки"""
        try:
            # Отримуємо інформацію про помилку
            error_info = {
                'error_type': type(error).__name__,
                'error_message': str(error),
                'timestamp': datetime.now().isoformat(),
                'traceback': traceback.format_exc(),
                'context': context
            }
            
            # Логуємо помилку
            self.logger.error(
                f"Error occurred: {error_info['error_type']}: {error_info['error_message']}",
                extra={'error_info': error_info}
            )
            
            # Шукаємо відповідний обробник
            handler = self._get_error_handler(error)
            if handler:
                # Викликаємо обробник
                result = await handler(error, error_info)
                error_info['handler_result'] = result
            
            # Відправляємо сповіщення
            if self.notification_callback:
                await self.notification_callback(error_info)
                
            return error_info
            
        except Exception as e:
            self.logger.critical(f"Error in error handler: {e}")
            return {
                'error_type': 'ErrorHandlerError',
                'error_message': str(e),
                'timestamp': datetime.now().isoformat(),
                'original_error': str(error)
            }
            
    def set_notification_callback(self, callback: Callable) -> None:
        """Встановлення функції для відправки сповіщень"""
        self.notification_callback = callback
        
    def _register_error_handlers(self) -> None:
        """Реєстрація обробників для різних типів помилок"""
        # Обробник для мережевих помилок
        self.error_handlers[ConnectionError] = self._handle_network_error
        
        # Обробник для помилок API
        self.error_handlers[ValueError] = self._handle_api_error
        
        # Обробник для помилок транзакцій
        self.error_handlers[Exception] = self._handle_transaction_error
        
    def _get_error_handler(self, error: Exception) -> Optional[Callable]:
        """Отримання відповідного обробника для помилки"""
        for error_type, handler in self.error_handlers.items():
            if isinstance(error, error_type):
                return handler
        return None
        
    async def _handle_network_error(self, error: Exception, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Обробка мережевих помилок"""
        result = {
            'action': 'retry',
            'retry_count': 0,
            'success': False
        }
        
        # Спроби повторного підключення
        for attempt in range(self.retry_attempts):
            try:
                result['retry_count'] = attempt + 1
                
                # TODO: Додати логіку повторного підключення
                # await reconnect()
                
                result['success'] = True
                break
                
            except Exception as e:
                self.logger.warning(f"Retry attempt {attempt + 1} failed: {e}")
                
        return result
        
    async def _handle_api_error(self, error: Exception, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Обробка помилок API"""
        result = {
            'action': 'validate',
            'validation_errors': [],
            'recommendations': []
        }
        
        # Аналіз помилки API
        if 'invalid parameter' in str(error).lower():
            result['validation_errors'].append('Invalid API parameters')
            result['recommendations'].append('Check API documentation for correct parameters')
            
        elif 'rate limit' in str(error).lower():
            result['validation_errors'].append('Rate limit exceeded')
            result['recommendations'].append('Implement rate limiting or increase limits')
            
        elif 'unauthorized' in str(error).lower():
            result['validation_errors'].append('Authentication failed')
            result['recommendations'].append('Check API keys and permissions')
            
        return result
        
    async def _handle_transaction_error(self, error: Exception, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Обробка помилок транзакцій"""
        result = {
            'action': 'analyze',
            'transaction_status': 'failed',
            'error_details': [],
            'recovery_options': []
        }
        
        # Аналіз помилки транзакції
        if 'insufficient funds' in str(error).lower():
            result['error_details'].append('Insufficient funds for transaction')
            result['recovery_options'].append('Check wallet balance')
            
        elif 'slippage' in str(error).lower():
            result['error_details'].append('Slippage tolerance exceeded')
            result['recovery_options'].append('Adjust slippage tolerance or try smaller amount')
            
        elif 'timeout' in str(error).lower():
            result['error_details'].append('Transaction timeout')
            result['recovery_options'].append('Check network status and try again')
            
        return result 