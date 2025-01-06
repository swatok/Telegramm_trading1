# Моніторинг бази даних

## Метрики бази даних

### Основні метрики

#### Конфігурація метрик
```python
class DatabaseMetricsConfig:
    """Конфігурація метрик бази даних"""
    
    def __init__(self):
        self.metrics = {
            'performance': True,
            'connections': True,
            'queries': True,
            'storage': True,
            'replication': True
        }
        self.thresholds = {
            'query_time_ms': 1000,
            'connection_count': 100,
            'storage_usage_percent': 80,
            'replication_lag_seconds': 300
        }
```

#### Колектор метрик
```python
class DatabaseMetricsCollector:
    """Збір метрик бази даних"""
    
    async def collect_metrics(self) -> Dict:
        """Збір метрик"""
        metrics = {}
        
        # Метрики продуктивності
        metrics['performance'] = await self._collect_performance_metrics()
        
        # Метрики з'єднань
        metrics['connections'] = await self._collect_connection_metrics()
        
        # Метрики запитів
        metrics['queries'] = await self._collect_query_metrics()
        
        # Метрики сховища
        metrics['storage'] = await self._collect_storage_metrics()
        
        # Метрики реплікації
        metrics['replication'] = await self._collect_replication_metrics()
        
        return metrics
        
    async def _collect_performance_metrics(self) -> Dict:
        """Збір метрик продуктивності"""
        return {
            'query_time': {
                'avg': await self._get_avg_query_time(),
                'max': await self._get_max_query_time(),
                'percentiles': await self._get_query_time_percentiles()
            },
            'throughput': {
                'queries_per_second': await self._get_queries_per_second(),
                'rows_per_second': await self._get_rows_per_second()
            },
            'cache': {
                'hit_ratio': await self._get_cache_hit_ratio(),
                'usage': await self._get_cache_usage()
            }
        }
```

### Моніторинг запитів

#### Монітор запитів
```python
class QueryMonitor:
    """Моніторинг запитів до бази даних"""
    
    async def monitor_queries(self) -> Dict:
        """Моніторинг запитів"""
        queries = await self._get_active_queries()
        
        return {
            'active_queries': len(queries),
            'by_type': self._group_by_type(queries),
            'by_duration': self._group_by_duration(queries),
            'slow_queries': self._get_slow_queries(queries),
            'blocked_queries': self._get_blocked_queries(queries)
        }
        
    def _get_slow_queries(
        self,
        queries: List[Dict]
    ) -> List[Dict]:
        """Отримання повільних запитів"""
        threshold = self.config.thresholds['query_time_ms']
        return [
            query for query in queries
            if query['duration'] > threshold
        ]
```

## Аналіз продуктивності

### Аналіз запитів

#### Аналізатор запитів
```python
class QueryAnalyzer:
    """Аналіз запитів до бази даних"""
    
    async def analyze_queries(
        self,
        period: str = '1h'
    ) -> Dict:
        """Аналіз запитів"""
        queries = await self._get_query_data(period)
        
        return {
            'summary': self._generate_summary(queries),
            'slow_queries': self._analyze_slow_queries(queries),
            'patterns': self._analyze_query_patterns(queries),
            'recommendations': self._generate_recommendations(queries)
        }
        
    def _analyze_slow_queries(
        self,
        queries: List[Dict]
    ) -> List[Dict]:
        """Аналіз повільних запитів"""
        slow_queries = []
        
        for query in queries:
            if query['duration'] > self.config.thresholds['query_time_ms']:
                analysis = {
                    'query': query['sql'],
                    'duration': query['duration'],
                    'execution_count': query['count'],
                    'tables': self._extract_tables(query['sql']),
                    'indexes': self._analyze_indexes(query),
                    'suggestions': self._generate_query_suggestions(query)
                }
                slow_queries.append(analysis)
                
        return slow_queries
```

### Аналіз індексів

#### Аналізатор індексів
```python
class IndexAnalyzer:
    """Аналіз індексів бази даних"""
    
    async def analyze_indexes(self) -> Dict:
        """Аналіз індексів"""
        indexes = await self._get_indexes()
        
        return {
            'unused_indexes': self._find_unused_indexes(indexes),
            'missing_indexes': await self._find_missing_indexes(),
            'duplicate_indexes': self._find_duplicate_indexes(indexes),
            'fragmented_indexes': self._find_fragmented_indexes(indexes)
        }
        
    async def _find_missing_indexes(self) -> List[Dict]:
        """Пошук відсутніх індексів"""
        missing_indexes = []
        
        # Отримання частих запитів
        queries = await self._get_frequent_queries()
        
        # Аналіз кожного запиту
        for query in queries:
            # Аналіз плану виконання
            plan = await self._get_execution_plan(query)
            
            # Пошук операцій послідовного сканування
            table_scans = self._find_table_scans(plan)
            
            if table_scans:
                missing_indexes.append({
                    'query': query,
                    'tables': table_scans,
                    'suggested_indexes': self._suggest_indexes(query, table_scans)
                })
                
        return missing_indexes
```

## Оптимізація

### Оптимізація запитів

#### Оптимізатор запитів
```python
class QueryOptimizer:
    """Оптимізація запитів до бази даних"""
    
    async def optimize_queries(self) -> Dict:
        """Оптимізація запитів"""
        optimizations = []
        
        # Отримання проблемних запитів
        queries = await self._get_problematic_queries()
        
        # Оптимізація кожного запиту
        for query in queries:
            optimization = await self._optimize_query(query)
            if optimization:
                optimizations.append(optimization)
                
        return {
            'optimizations_found': len(optimizations),
            'details': optimizations,
            'estimated_improvement': self._estimate_improvement(optimizations)
        }
        
    async def _optimize_query(self, query: Dict) -> Optional[Dict]:
        """Оптимізація запиту"""
        # Аналіз плану виконання
        plan = await self._get_execution_plan(query['sql'])
        
        optimizations = []
        
        # Оптимізація індексів
        index_opts = self._optimize_indexes(plan)
        if index_opts:
            optimizations.extend(index_opts)
            
        # Оптимізація з'єднань
        join_opts = self._optimize_joins(plan)
        if join_opts:
            optimizations.extend(join_opts)
            
        # Оптимізація умов
        where_opts = self._optimize_where_clauses(plan)
        if where_opts:
            optimizations.extend(where_opts)
            
        if optimizations:
            return {
                'query': query,
                'optimizations': optimizations,
                'estimated_improvement': self._estimate_query_improvement(
                    query,
                    optimizations
                )
            }
            
        return None
```

### Оптимізація індексів

#### Оптимізатор індексів
```python
class IndexOptimizer:
    """Оптимізація індексів бази даних"""
    
    async def optimize_indexes(self) -> Dict:
        """Оптимізація індексів"""
        # Отримання поточного стану
        current_state = await self._get_index_state()
        
        optimizations = []
        
        # Видалення невикористовуваних індексів
        unused = await self._remove_unused_indexes()
        if unused:
            optimizations.extend(unused)
            
        # Створення відсутніх індексів
        missing = await self._create_missing_indexes()
        if missing:
            optimizations.extend(missing)
            
        # Реорганізація фрагментованих індексів
        fragmented = await self._reorganize_fragmented_indexes()
        if fragmented:
            optimizations.extend(fragmented)
            
        return {
            'previous_state': current_state,
            'optimizations': optimizations,
            'new_state': await self._get_index_state()
        }
``` 