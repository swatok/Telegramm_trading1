# Моніторинг безпеки

## Аудит безпеки

### Логування подій безпеки

#### Конфігурація аудиту
```python
class SecurityAuditConfig:
    """Конфігурація системи аудиту безпеки"""
    
    def __init__(self):
        self.audit_events = {
            'authentication': True,
            'authorization': True,
            'data_access': True,
            'configuration_changes': True,
            'system_events': True
        }
        self.retention = {
            'audit_logs': 90,  # днів
            'security_events': 180,  # днів
            'access_logs': 30  # днів
        }
```

#### Логер безпеки
```python
class SecurityLogger:
    """Логування подій безпеки"""
    
    def log_security_event(
        self,
        event_type: str,
        severity: str,
        details: Dict
    ):
        """Логування події безпеки"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'severity': severity,
            'details': details,
            'source_ip': self._get_source_ip(),
            'user_agent': self._get_user_agent()
        }
        
        # Збереження в лог
        self.logger.log(
            self._get_log_level(severity),
            json.dumps(event)
        )
        
        # Відправка сповіщення якщо критична подія
        if severity in ['critical', 'high']:
            self._send_security_alert(event)
```

### Моніторинг загроз

#### Детектор загроз
```python
class ThreatDetector:
    """Виявлення загроз безпеки"""
    
    async def analyze_threats(self):
        """Аналіз потенційних загроз"""
        threats = []
        
        # Перевірка підозрілої активності
        suspicious = await self._check_suspicious_activity()
        if suspicious:
            threats.extend(suspicious)
            
        # Перевірка аномалій
        anomalies = await self._detect_anomalies()
        if anomalies:
            threats.extend(anomalies)
            
        # Перевірка відомих атак
        attacks = await self._check_known_attacks()
        if attacks:
            threats.extend(attacks)
            
        return threats
        
    async def _check_suspicious_activity(self) -> List[Dict]:
        """Перевірка підозрілої активності"""
        suspicious = []
        
        # Перевірка частих невдалих спроб входу
        login_attempts = await self._get_failed_logins()
        if self._is_brute_force_attempt(login_attempts):
            suspicious.append({
                'type': 'brute_force',
                'severity': 'high',
                'details': login_attempts
            })
            
        # Перевірка підозрілих IP
        suspicious_ips = await self._check_ip_reputation()
        if suspicious_ips:
            suspicious.append({
                'type': 'suspicious_ip',
                'severity': 'medium',
                'details': suspicious_ips
            })
            
        return suspicious
```

## Контроль доступу

### Управління доступом

#### Менеджер доступу
```python
class AccessManager:
    """Управління контролем доступу"""
    
    async def check_access(
        self,
        user: User,
        resource: str,
        action: str
    ) -> bool:
        """Перевірка прав доступу"""
        # Перевірка базових прав
        if not await self._check_basic_access(user, resource):
            return False
            
        # Перевірка специфічних прав
        if not await self._check_specific_permissions(user, resource, action):
            return False
            
        # Перевірка обмежень
        if await self._check_restrictions(user, resource):
            return False
            
        return True
        
    async def _check_basic_access(self, user: User, resource: str) -> bool:
        """Перевірка базових прав доступу"""
        # Перевірка активності користувача
        if not user.is_active:
            return False
            
        # Перевірка базових ролей
        if not self._has_required_roles(user, resource):
            return False
            
        return True
```

### Автентифікація

#### Менеджер автентифікації
```python
class AuthenticationManager:
    """Управління автентифікацією"""
    
    async def authenticate(
        self,
        credentials: Dict
    ) -> Optional[User]:
        """Автентифікація користувача"""
        # Валідація креденшалів
        if not self._validate_credentials(credentials):
            return None
            
        # Пошук користувача
        user = await self._find_user(credentials)
        if not user:
            return None
            
        # Перевірка паролю
        if not await self._verify_password(
            credentials['password'],
            user.password_hash
        ):
            return None
            
        # Оновлення даних входу
        await self._update_login_info(user)
        
        return user
        
    def _validate_credentials(self, credentials: Dict) -> bool:
        """Валідація креденшалів"""
        required = ['username', 'password']
        return all(field in credentials for field in required)
```

## Шифрування

### Управління ключами

#### Менеджер ключів
```python
class KeyManager:
    """Управління криптографічними ключами"""
    
    def __init__(self):
        self.key_store = {
            'encryption_keys': {},
            'signing_keys': {},
            'master_keys': {}
        }
        
    async def get_key(
        self,
        key_type: str,
        key_id: str
    ) -> Optional[bytes]:
        """Отримання ключа"""
        if key_type not in self.key_store:
            raise InvalidKeyTypeError()
            
        # Пошук ключа
        key = self.key_store[key_type].get(key_id)
        if not key:
            return None
            
        # Перевірка терміну дії
        if self._is_key_expired(key):
            await self._rotate_key(key_type, key_id)
            key = self.key_store[key_type][key_id]
            
        return key
        
    async def _rotate_key(self, key_type: str, key_id: str):
        """Ротація ключа"""
        # Генерація нового ключа
        new_key = self._generate_key()
        
        # Збереження старого ключа
        old_key = self.key_store[key_type][key_id]
        self._archive_key(old_key)
        
        # Оновлення ключа
        self.key_store[key_type][key_id] = new_key
```

### Шифрування даних

#### Менеджер шифрування
```python
class EncryptionManager:
    """Управління шифруванням даних"""
    
    async def encrypt_data(
        self,
        data: bytes,
        key_id: str
    ) -> Dict:
        """Шифрування даних"""
        # Отримання ключа
        key = await self.key_manager.get_key('encryption_keys', key_id)
        if not key:
            raise KeyNotFoundError()
            
        # Генерація IV
        iv = self._generate_iv()
        
        # Шифрування
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Додавання AAD
        aad = self._generate_aad()
        encryptor.authenticate_additional_data(aad)
        
        # Шифрування даних
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        return {
            'ciphertext': ciphertext,
            'iv': iv,
            'tag': encryptor.tag,
            'aad': aad,
            'key_id': key_id
        }
```

## Моніторинг вразливостей

### Сканування вразливостей

#### Сканер вразливостей
```python
class VulnerabilityScanner:
    """Сканування вразливостей системи"""
    
    async def scan_system(self) -> Dict:
        """Сканування системи"""
        vulnerabilities = []
        
        # Сканування залежностей
        deps = await self._scan_dependencies()
        if deps:
            vulnerabilities.extend(deps)
            
        # Сканування конфігурації
        config = await self._scan_configuration()
        if config:
            vulnerabilities.extend(config)
            
        # Сканування коду
        code = await self._scan_code()
        if code:
            vulnerabilities.extend(code)
            
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'vulnerabilities': vulnerabilities,
            'summary': self._generate_summary(vulnerabilities)
        }
        
    def _generate_summary(self, vulnerabilities: List[Dict]) -> Dict:
        """Генерація зведення по вразливостям"""
        return {
            'total': len(vulnerabilities),
            'by_severity': self._count_by_severity(vulnerabilities),
            'by_type': self._count_by_type(vulnerabilities),
            'critical': self._get_critical_vulnerabilities(vulnerabilities)
        }
```

### Управління патчами

#### Менеджер патчів
```python
class PatchManager:
    """Управління оновленнями безпеки"""
    
    async def check_updates(self) -> Dict:
        """Перевірка доступних оновлень"""
        updates = []
        
        # Перевірка системних оновлень
        system = await self._check_system_updates()
        if system:
            updates.extend(system)
            
        # Перевірка оновлень залежностей
        deps = await self._check_dependency_updates()
        if deps:
            updates.extend(deps)
            
        return {
            'available_updates': updates,
            'critical_updates': self._filter_critical(updates),
            'recommended_actions': self._generate_recommendations(updates)
        }
        
    def _filter_critical(self, updates: List[Dict]) -> List[Dict]:
        """Фільтрація критичних оновлень"""
        return [
            update for update in updates
            if update['severity'] == 'critical'
        ]
``` 