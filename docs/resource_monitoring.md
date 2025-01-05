# Моніторинг системних ресурсів

## Метрики ресурсів

### Основні метрики

#### Конфігурація метрик
```python
class ResourceMetricsConfig:
    """Конфігурація метрик системних ресурсів"""
    
    def __init__(self):
        self.metrics = {
            'cpu': True,
            'memory': True,
            'disk': True,
            'network': True,
            'process': True
        }
        self.thresholds = {
            'cpu_percent': 80,
            'memory_percent': 90,
            'disk_usage_percent': 85,
            'disk_io_util': 70,
            'network_util': 75
        }
```

#### Колектор метрик
```python
class ResourceMetricsCollector:
    """Збір метрик системних ресурсів"""
    
    async def collect_metrics(self) -> Dict:
        """Збір метрик"""
        metrics = {}
        
        # CPU метрики
        metrics['cpu'] = await self._collect_cpu_metrics()
        
        # Метрики пам'яті
        metrics['memory'] = await self._collect_memory_metrics()
        
        # Дискові метрики
        metrics['disk'] = await self._collect_disk_metrics()
        
        # Мережеві метрики
        metrics['network'] = await self._collect_network_metrics()
        
        # Метрики процесів
        metrics['process'] = await self._collect_process_metrics()
        
        return metrics
        
    async def _collect_cpu_metrics(self) -> Dict:
        """Збір CPU метрик"""
        cpu_times = psutil.cpu_times_percent()
        cpu_freq = psutil.cpu_freq()
        
        return {
            'usage_percent': psutil.cpu_percent(interval=1),
            'per_cpu_percent': psutil.cpu_percent(interval=1, percpu=True),
            'times': {
                'user': cpu_times.user,
                'system': cpu_times.system,
                'idle': cpu_times.idle,
                'iowait': cpu_times.iowait
            },
            'frequency': {
                'current': cpu_freq.current,
                'min': cpu_freq.min,
                'max': cpu_freq.max
            },
            'load_average': os.getloadavg()
        }
```

### Моніторинг процесів

#### Монітор процесів
```python
class ProcessMonitor:
    """Моніторинг системних процесів"""
    
    async def monitor_processes(self) -> Dict:
        """Моніторинг процесів"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                # Отримання інформації про процес
                proc_info = proc.info
                proc_info['cpu_percent'] = proc.cpu_percent()
                proc_info['memory_percent'] = proc.memory_percent()
                
                processes.append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        return {
            'total_processes': len(processes),
            'top_cpu_processes': self._get_top_processes(processes, 'cpu_percent'),
            'top_memory_processes': self._get_top_processes(processes, 'memory_percent'),
            'process_stats': self._calculate_process_stats(processes)
        }
        
    def _get_top_processes(
        self,
        processes: List[Dict],
        sort_key: str,
        limit: int = 10
    ) -> List[Dict]:
        """Отримання топ процесів"""
        return sorted(
            processes,
            key=lambda x: x[sort_key],
            reverse=True
        )[:limit]
```

## Аналіз використання

### Аналіз CPU

#### Аналізатор CPU
```python
class CPUAnalyzer:
    """Аналіз використання CPU"""
    
    async def analyze_cpu_usage(
        self,
        period: str = '1h'
    ) -> Dict:
        """Аналіз використання CPU"""
        usage_data = await self._get_cpu_usage_data(period)
        
        return {
            'current_usage': self._get_current_usage(),
            'average_usage': self._calculate_average(usage_data),
            'peak_usage': self._find_peak_usage(usage_data),
            'bottlenecks': self._identify_bottlenecks(usage_data),
            'recommendations': self._generate_recommendations(usage_data)
        }
        
    def _identify_bottlenecks(self, data: List[Dict]) -> List[Dict]:
        """Виявлення вузьких місць"""
        bottlenecks = []
        
        # Перевірка високого навантаження
        if self._has_high_load(data):
            bottlenecks.append({
                'type': 'high_load',
                'severity': 'high',
                'details': self._get_load_details(data)
            })
            
        # Перевірка IO wait
        if self._has_high_iowait(data):
            bottlenecks.append({
                'type': 'high_iowait',
                'severity': 'medium',
                'details': self._get_iowait_details(data)
            })
            
        return bottlenecks
```

### Аналіз пам'яті

#### Аналізатор пам'яті
```python
class MemoryAnalyzer:
    """Аналіз використання пам'яті"""
    
    async def analyze_memory_usage(
        self,
        period: str = '1h'
    ) -> Dict:
        """Аналіз використання пам'яті"""
        usage_data = await self._get_memory_usage_data(period)
        
        return {
            'current_usage': self._get_current_usage(),
            'usage_breakdown': self._analyze_usage_breakdown(),
            'swap_usage': self._analyze_swap_usage(),
            'issues': self._identify_issues(usage_data),
            'recommendations': self._generate_recommendations(usage_data)
        }
        
    def _analyze_usage_breakdown(self) -> Dict:
        """Аналіз розподілу використання пам'яті"""
        mem = psutil.virtual_memory()
        return {
            'total': mem.total,
            'available': mem.available,
            'used': mem.used,
            'free': mem.free,
            'cached': mem.cached,
            'buffers': mem.buffers,
            'shared': mem.shared
        }
```

## Оптимізація

### Оптимізація ресурсів

#### Оптимізатор ресурсів
```python
class ResourceOptimizer:
    """Оптимізація використання системних ресурсів"""
    
    async def optimize_resources(self) -> Dict:
        """Оптимізація ресурсів"""
        # Отримання поточного стану
        current_state = await self._get_resource_state()
        
        optimizations = []
        
        # Оптимізація CPU
        cpu_opts = await self._optimize_cpu_usage()
        if cpu_opts:
            optimizations.extend(cpu_opts)
            
        # Оптимізація пам'яті
        memory_opts = await self._optimize_memory_usage()
        if memory_opts:
            optimizations.extend(memory_opts)
            
        # Оптимізація диску
        disk_opts = await self._optimize_disk_usage()
        if disk_opts:
            optimizations.extend(disk_opts)
            
        return {
            'previous_state': current_state,
            'optimizations': optimizations,
            'new_state': await self._get_resource_state()
        }
        
    async def _optimize_cpu_usage(self) -> List[Dict]:
        """Оптимізація використання CPU"""
        optimizations = []
        
        # Аналіз процесів
        processes = await self._analyze_processes()
        
        # Оптимізація пріоритетів
        if processes['high_priority_count'] > self.config.max_high_priority:
            optimizations.append({
                'type': 'process_priority',
                'action': 'adjust_priorities',
                'details': {
                    'processes': processes['high_priority_processes'],
                    'new_priority': 'normal'
                }
            })
            
        # Оптимізація афінності
        if processes['cpu_bound_count'] > self.config.max_cpu_bound:
            optimizations.append({
                'type': 'cpu_affinity',
                'action': 'distribute_load',
                'details': {
                    'processes': processes['cpu_bound_processes'],
                    'target_cores': self._get_target_cores()
                }
            })
            
        return optimizations
```

### Управління ресурсами

#### Менеджер ресурсів
```python
class ResourceManager:
    """Управління системними ресурсами"""
    
    async def manage_resources(self) -> Dict:
        """Управління ресурсами"""
        # Отримання метрик
        metrics = await self._get_resource_metrics()
        
        actions = []
        
        # Перевірка порогових значень
        if self._check_thresholds(metrics):
            # Виконання дій по управлінню
            actions = await self._take_management_actions(metrics)
            
        return {
            'metrics': metrics,
            'actions_taken': actions,
            'status': self._get_current_status()
        }
        
    def _check_thresholds(self, metrics: Dict) -> bool:
        """Перевірка порогових значень"""
        # Перевірка CPU
        if metrics['cpu']['usage_percent'] > self.config.thresholds['cpu_percent']:
            return True
            
        # Перевірка пам'яті
        if metrics['memory']['usage_percent'] > self.config.thresholds['memory_percent']:
            return True
            
        # Перевірка диску
        if metrics['disk']['usage_percent'] > self.config.thresholds['disk_usage_percent']:
            return True
            
        return False
``` 