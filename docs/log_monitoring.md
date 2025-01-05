# Моніторинг логів

## Конфігурація логування

### Налаштування логгера

#### Базова конфігурація
```python
class LoggingConfig:
    """Конфігурація системи логування"""
    
    def __init__(self):
        self.log_levels = {
            'production': logging.INFO,
            'development': logging.DEBUG,
            'testing': logging.DEBUG
        }
        self.handlers = {
            'console': {
                'enabled': True,
                'level': logging.INFO,
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
            'file': {
                'enabled': True,
                'level': logging.DEBUG,
                'filename': 'app.log',
                'max_size': 10485760,  # 10MB
                'backup_count': 5,
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
            'syslog': {
                'enabled': True,
                'level': logging.WARNING,
                'address': '/dev/log',
                'facility': 'local0',
                'format': '%(name)s: %(message)s'
            }
        }
```

#### Форматування логів
```python
class LogFormatter:
    """Форматування логів"""
    
    def __init__(self):
        self.formatters = {
            'default': logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            ),
            'detailed': logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s '
                '[%(filename)s:%(lineno)d]: %(message)s'
            ),
            'json': JsonFormatter(
                '%(timestamp)s %(level)s %(name)s %(message)s'
            )
        }
        
    def get_formatter(
        self,
        format_type: str = 'default'
    ) -> logging.Formatter:
        """Отримання форматера"""
        return self.formatters.get(
            format_type,
            self.formatters['default']
        )
```

## Збір логів

### Агрегація логів

#### Агрегатор логів
```python
class LogAggregator:
    """Агрегація логів з різних джерел"""
    
    async def aggregate_logs(
        self,
        period: str = '1h'
    ) -> Dict:
        """Агрегація логів"""
        logs = []
        
        # Збір логів з файлів
        file_logs = await self._collect_file_logs(period)
        if file_logs:
            logs.extend(file_logs)
            
        # Збір логів з syslog
        syslog_logs = await self._collect_syslog_logs(period)
        if syslog_logs:
            logs.extend(syslog_logs)
            
        # Збір логів з journald
        journal_logs = await self._collect_journal_logs(period)
        if journal_logs:
            logs.extend(journal_logs)
            
        return {
            'total_logs': len(logs),
            'logs_by_level': self._group_by_level(logs),
            'logs_by_source': self._group_by_source(logs),
            'logs_by_time': self._group_by_time(logs)
        }
```

### Фільтрація логів

#### Фільтр логів
```python
class LogFilter:
    """Фільтрація логів"""
    
    def filter_logs(
        self,
        logs: List[Dict],
        filters: Dict
    ) -> List[Dict]:
        """Фільтрація логів"""
        filtered_logs = logs
        
        # Фільтрація за рівнем
        if 'level' in filters:
            filtered_logs = self._filter_by_level(
                filtered_logs,
                filters['level']
            )
            
        # Фільтрація за джерелом
        if 'source' in filters:
            filtered_logs = self._filter_by_source(
                filtered_logs,
                filters['source']
            )
            
        # Фільтрація за часом
        if 'time_range' in filters:
            filtered_logs = self._filter_by_time(
                filtered_logs,
                filters['time_range']
            )
            
        # Фільтрація за шаблоном
        if 'pattern' in filters:
            filtered_logs = self._filter_by_pattern(
                filtered_logs,
                filters['pattern']
            )
            
        return filtered_logs
```

## Аналіз логів

### Аналіз патернів

#### Аналізатор патернів
```python
class LogPatternAnalyzer:
    """Аналіз патернів в логах"""
    
    async def analyze_patterns(
        self,
        logs: List[Dict]
    ) -> Dict:
        """Аналіз патернів"""
        patterns = {
            'error_patterns': self._analyze_error_patterns(logs),
            'warning_patterns': self._analyze_warning_patterns(logs),
            'access_patterns': self._analyze_access_patterns(logs),
            'timing_patterns': self._analyze_timing_patterns(logs)
        }
        
        return {
            'patterns': patterns,
            'anomalies': self._detect_anomalies(patterns),
            'trends': self._analyze_trends(patterns),
            'recommendations': self._generate_recommendations(patterns)
        }
        
    def _analyze_error_patterns(
        self,
        logs: List[Dict]
    ) -> List[Dict]:
        """Аналіз патернів помилок"""
        error_logs = [
            log for log in logs
            if log['level'] in ['ERROR', 'CRITICAL']
        ]
        
        patterns = []
        for error in error_logs:
            pattern = self._extract_error_pattern(error)
            if pattern:
                patterns.append({
                    'pattern': pattern,
                    'count': self._count_pattern_occurrences(pattern, error_logs),
                    'first_seen': self._get_first_occurrence(pattern, error_logs),
                    'last_seen': self._get_last_occurrence(pattern, error_logs)
                })
                
        return patterns
```

### Аналіз аномалій

#### Детектор аномалій
```python
class LogAnomalyDetector:
    """Виявлення аномалій в логах"""
    
    def detect_anomalies(
        self,
        logs: List[Dict]
    ) -> List[Dict]:
        """Виявлення аномалій"""
        anomalies = []
        
        # Аналіз частоти
        frequency_anomalies = self._detect_frequency_anomalies(logs)
        if frequency_anomalies:
            anomalies.extend(frequency_anomalies)
            
        # Аналіз патернів
        pattern_anomalies = self._detect_pattern_anomalies(logs)
        if pattern_anomalies:
            anomalies.extend(pattern_anomalies)
            
        # Аналіз послідовностей
        sequence_anomalies = self._detect_sequence_anomalies(logs)
        if sequence_anomalies:
            anomalies.extend(sequence_anomalies)
            
        return anomalies
        
    def _detect_frequency_anomalies(
        self,
        logs: List[Dict]
    ) -> List[Dict]:
        """Виявлення аномалій частоти"""
        anomalies = []
        
        # Групування за часом
        grouped_logs = self._group_by_time_window(logs)
        
        # Розрахунок базової лінії
        baseline = self._calculate_frequency_baseline(grouped_logs)
        
        # Виявлення відхилень
        for window, count in grouped_logs.items():
            if abs(count - baseline['mean']) > 3 * baseline['std_dev']:
                anomalies.append({
                    'type': 'frequency_anomaly',
                    'window': window,
                    'count': count,
                    'baseline': baseline,
                    'deviation': abs(count - baseline['mean'])
                })
                
        return anomalies
```

## Візуалізація

### Графіки логів

#### Генератор графіків
```python
class LogVisualizer:
    """Візуалізація логів"""
    
    def create_visualizations(
        self,
        logs: List[Dict]
    ) -> Dict:
        """Створення візуалізацій"""
        return {
            'time_distribution': self._create_time_distribution(logs),
            'level_distribution': self._create_level_distribution(logs),
            'error_trends': self._create_error_trends(logs),
            'performance_graphs': self._create_performance_graphs(logs)
        }
        
    def _create_time_distribution(
        self,
        logs: List[Dict]
    ) -> Dict:
        """Створення розподілу за часом"""
        # Групування за часом
        grouped = self._group_by_time_window(logs)
        
        # Створення графіку
        plt.figure(figsize=(12, 6))
        plt.plot(grouped.keys(), grouped.values())
        plt.title('Log Distribution Over Time')
        plt.xlabel('Time')
        plt.ylabel('Log Count')
        plt.grid(True)
        
        return {
            'plot': plt,
            'data': grouped
        }
```

### Дашборди

#### Конфігурація дашборду
```python
class LogDashboard:
    """Конфігурація дашборду логів"""
    
    def get_dashboard_config(self) -> Dict:
        """Отримання конфігурації дашборду"""
        return {
            'title': 'Log Monitoring Dashboard',
            'refresh_rate': 60,  # секунд
            'panels': [
                {
                    'title': 'Log Volume',
                    'type': 'graph',
                    'datasource': 'elasticsearch',
                    'targets': [{
                        'query': 'count(*) by time',
                        'interval': '1m'
                    }]
                },
                {
                    'title': 'Error Rate',
                    'type': 'graph',
                    'datasource': 'elasticsearch',
                    'targets': [{
                        'query': 'count(*) by level="ERROR"',
                        'interval': '1m'
                    }]
                },
                {
                    'title': 'Top Error Messages',
                    'type': 'table',
                    'datasource': 'elasticsearch',
                    'targets': [{
                        'query': 'top 10 message where level="ERROR"'
                    }]
                }
            ]
        }
``` 