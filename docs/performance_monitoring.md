# Моніторинг продуктивності

## Метрики продуктивності

### Основні метрики

#### Метрики часу виконання
```python
class ExecutionMetrics:
    """Метрики часу виконання операцій"""
    
    def __init__(self):
        self.execution_time = Histogram(
            'operation_execution_time_seconds',
            'Operation execution time in seconds',
            ['operation']
        )
        self.operation_count = Counter(
            'operation_count_total',
            'Total number of operations',
            ['operation', 'status']
        )
        
    def record_execution(self, operation: str, duration: float, success: bool):
        """Запис метрик виконання"""
        self.execution_time.labels(operation=operation).observe(duration)
        status = 'success' if success else 'failure'
        self.operation_count.labels(operation=operation, status=status).inc()
```

#### Метрики ресурсів
```python
class ResourceMetrics:
    """Метрики використання ресурсів"""
    
    def __init__(self):
        self.memory_usage = Gauge(
            'memory_usage_bytes',
            'Memory usage in bytes'
        )
        self.cpu_usage = Gauge(
            'cpu_usage_percent',
            'CPU usage percentage'
        )
        self.disk_io = Counter(
            'disk_io_bytes',
            'Disk I/O in bytes',
            ['operation']
        )
        
    def update_resource_usage(self):
        """Оновлення метрик використання ресурсів"""
        process = psutil.Process()
        self.memory_usage.set(process.memory_info().rss)
        self.cpu_usage.set(process.cpu_percent())
```

### Профілювання

#### Профілювання коду
```python
class CodeProfiler:
    """Профілювання виконання коду"""
    
    def __init__(self):
        self.profiler = cProfile.Profile()
        
    def start_profiling(self):
        """Початок профілювання"""
        self.profiler.enable()
        
    def stop_profiling(self) -> Dict:
        """Завершення профілювання"""
        self.profiler.disable()
        stats = pstats.Stats(self.profiler)
        return {
            'total_calls': stats.total_calls,
            'total_time': stats.total_tt,
            'calls': self._get_top_calls(stats)
        }
        
    def _get_top_calls(self, stats: pstats.Stats, limit: int = 10) -> List[Dict]:
        """Отримання топ викликів"""
        return [{
            'function': func,
            'calls': stats.stats[func][0],
            'time': stats.stats[func][3]
        } for func in sorted(
            stats.stats,
            key=lambda x: stats.stats[x][3],
            reverse=True
        )[:limit]]
```

## Оптимізація

### Аналіз вузьких місць

#### Аналізатор продуктивності
```python
class PerformanceAnalyzer:
    """Аналіз продуктивності системи"""
    
    async def analyze_bottlenecks(self):
        """Аналіз вузьких місць"""
        metrics = await self._get_performance_metrics()
        
        bottlenecks = []
        
        # Аналіз часу виконання
        slow_operations = self._find_slow_operations(
            metrics['execution_times']
        )
        if slow_operations:
            bottlenecks.extend(slow_operations)
            
        # Аналіз використання ресурсів
        resource_issues = self._check_resource_usage(
            metrics['resource_usage']
        )
        if resource_issues:
            bottlenecks.extend(resource_issues)
            
        return bottlenecks
        
    def _find_slow_operations(self, execution_times: Dict) -> List[Dict]:
        """Пошук повільних операцій"""
        threshold = statistics.mean(execution_times.values()) * 2
        return [{
            'type': 'slow_operation',
            'operation': op,
            'time': time,
            'threshold': threshold
        } for op, time in execution_times.items() if time > threshold]
        
    def _check_resource_usage(self, usage: Dict) -> List[Dict]:
        """Перевірка використання ресурсів"""
        issues = []
        
        if usage['memory'] > 90:  # 90% використання пам'яті
            issues.append({
                'type': 'high_memory',
                'usage': usage['memory'],
                'threshold': 90
            })
            
        if usage['cpu'] > 80:  # 80% використання CPU
            issues.append({
                'type': 'high_cpu',
                'usage': usage['cpu'],
                'threshold': 80
            })
            
        return issues
```

### Оптимізація запитів

#### Оптимізатор запитів
```python
class QueryOptimizer:
    """Оптимізація запитів до API"""
    
    def analyze_query(self, query: Dict) -> Dict:
        """Аналіз та оптимізація запиту"""
        optimizations = []
        
        # Перевірка параметрів
        param_opts = self._optimize_parameters(query['parameters'])
        if param_opts:
            optimizations.extend(param_opts)
            
        # Перевірка фільтрів
        filter_opts = self._optimize_filters(query['filters'])
        if filter_opts:
            optimizations.extend(filter_opts)
            
        # Перевірка сортування
        sort_opts = self._optimize_sorting(query['sort'])
        if sort_opts:
            optimizations.extend(sort_opts)
            
        return {
            'original_query': query,
            'optimizations': optimizations,
            'estimated_improvement': self._estimate_improvement(optimizations)
        }
        
    def _optimize_parameters(self, parameters: Dict) -> List[Dict]:
        """Оптимізація параметрів запиту"""
        optimizations = []
        
        # Перевірка зайвих полів
        unused_fields = self._find_unused_fields(parameters)
        if unused_fields:
            optimizations.append({
                'type': 'remove_fields',
                'fields': unused_fields
            })
            
        # Перевірка розміру сторінки
        if 'page_size' in parameters:
            opt_size = self._optimize_page_size(parameters['page_size'])
            if opt_size != parameters['page_size']:
                optimizations.append({
                    'type': 'adjust_page_size',
                    'from': parameters['page_size'],
                    'to': opt_size
                })
                
        return optimizations
```

## Кешування

### Конфігурація кешу

#### Налаштування кешування
```python
class CacheConfig:
    """Конфігурація системи кешування"""
    
    def __init__(self):
        self.settings = {
            'default_ttl': 300,  # 5 хвилин
            'max_size': 1000,    # Максимальна кількість елементів
            'eviction_policy': 'lru'  # Least Recently Used
        }
        self.backends = {
            'memory': {
                'enabled': True,
                'max_size': 100_000_000  # 100MB
            },
            'redis': {
                'enabled': True,
                'host': 'localhost',
                'port': 6379,
                'db': 0
            }
        }
```

### Управління кешем

#### Менеджер кешу
```python
class CacheManager:
    """Управління кешуванням"""
    
    async def get_cached(self, key: str) -> Optional[Any]:
        """Отримання даних з кешу"""
        # Спроба отримати з memory cache
        value = self.memory_cache.get(key)
        if value is not None:
            return value
            
        # Спроба отримати з Redis
        value = await self.redis.get(key)
        if value is not None:
            # Оновлення memory cache
            self.memory_cache.set(key, value)
            return value
            
        return None
        
    async def set_cached(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """Збереження даних в кеш"""
        ttl = ttl or self.config.settings['default_ttl']
        
        # Збереження в memory cache
        self.memory_cache.set(key, value, ttl)
        
        # Збереження в Redis
        await self.redis.set(key, value, ttl)
        
    async def invalidate(self, pattern: str):
        """Інвалідація кешу"""
        # Очищення memory cache
        self.memory_cache.delete_pattern(pattern)
        
        # Очищення Redis
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
```

## Масштабування

### Горизонтальне масштабування

#### Конфігурація масштабування
```python
class ScalingConfig:
    """Конфігурація масштабування"""
    
    def __init__(self):
        self.thresholds = {
            'cpu_threshold': 80,     # 80% CPU
            'memory_threshold': 90,   # 90% RAM
            'request_threshold': 1000 # запитів/сек
        }
        self.scaling = {
            'min_instances': 2,
            'max_instances': 10,
            'scale_up_factor': 1.5,   # Збільшення на 50%
            'scale_down_factor': 0.5  # Зменшення на 50%
        }
```

### Балансування навантаження

#### Балансувальник навантаження
```python
class LoadBalancer:
    """Балансування навантаження"""
    
    async def distribute_request(self, request: Request) -> str:
        """Вибір сервера для обробки запиту"""
        servers = await self._get_available_servers()
        
        # Фільтрація перевантажених серверів
        available = [
            server for server in servers
            if not self._is_overloaded(server)
        ]
        
        if not available:
            raise NoAvailableServersError()
            
        # Вибір сервера за алгоритмом Round Robin
        server = self._round_robin_select(available)
        
        # Оновлення статистики
        await self._update_server_stats(server)
        
        return server
        
    def _is_overloaded(self, server: Dict) -> bool:
        """Перевірка перевантаження сервера"""
        return (
            server['cpu_usage'] > self.config.thresholds['cpu_threshold'] or
            server['memory_usage'] > self.config.thresholds['memory_threshold'] or
            server['requests_per_second'] > self.config.thresholds['request_threshold']
        )
``` 