# Безпека системи

## Аутентифікація та авторизація

### Управління доступом
```python
class AccessManager:
    def check_access(self, user, resource):
        """Перевірка прав доступу"""
        if not self._is_authenticated(user):
            raise AuthenticationError("User not authenticated")
            
        if not self._has_permission(user, resource):
            raise AuthorizationError("Access denied")
            
        return True
```

### Токени доступу
```python
class TokenManager:
    def generate_token(self, user_id: str) -> str:
        """Генерація токену доступу"""
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(days=1)
        }
        return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        
    def validate_token(self, token: str) -> bool:
        """Валідація токену"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return True
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError()
        except jwt.InvalidTokenError:
            raise InvalidTokenError()
```

## Шифрування даних

### Шифрування в спокої
```python
class DataEncryption:
    def encrypt_data(self, data: str) -> str:
        """Шифрування даних"""
        key = Fernet.generate_key()
        f = Fernet(key)
        return f.encrypt(data.encode())
        
    def decrypt_data(self, encrypted_data: bytes) -> str:
        """Розшифрування даних"""
        f = Fernet(key)
        return f.decrypt(encrypted_data).decode()
```

### Шифрування в русі
```python
class TransportEncryption:
    def encrypt_message(self, message: str) -> str:
        """Шифрування повідомлення"""
        return self._ssl_encrypt(message)
        
    def decrypt_message(self, encrypted_message: str) -> str:
        """Розшифрування повідомлення"""
        return self._ssl_decrypt(encrypted_message)
```

## Захист від атак

### Захист від SQL-ін'єкцій
```python
class SQLInjectionProtection:
    def sanitize_input(self, query: str) -> str:
        """Санітизація SQL-запиту"""
        return re.sub(r'[^\w\s-]', '', query)
        
    def use_parameterized_query(self, query: str, params: Dict):
        """Використання параметризованих запитів"""
        return self.cursor.execute(query, params)
```

### Захист від XSS
```python
class XSSProtection:
    def sanitize_html(self, content: str) -> str:
        """Санітизація HTML"""
        return bleach.clean(content)
        
    def encode_output(self, content: str) -> str:
        """Кодування виводу"""
        return html.escape(content)
```

## Моніторинг безпеки

### Логування подій безпеки
```python
class SecurityLogger:
    def log_security_event(self, event_type: str, details: Dict):
        """Логування події безпеки"""
        log_entry = {
            "timestamp": datetime.utcnow(),
            "type": event_type,
            "details": details
        }
        self.security_logs.insert_one(log_entry)
```

### Виявлення аномалій
```python
class AnomalyDetection:
    def detect_anomalies(self, events: List[Dict]) -> List[Dict]:
        """Виявлення аномальної активності"""
        anomalies = []
        for event in events:
            if self._is_anomalous(event):
                anomalies.append(event)
        return anomalies
```

## Управління ключами

### Генерація ключів
```python
class KeyGenerator:
    def generate_key_pair(self) -> Tuple[str, str]:
        """Генерація пари ключів"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()
        return private_key, public_key
```

### Ротація ключів
```python
class KeyRotation:
    def rotate_keys(self):
        """Ротація ключів"""
        new_keys = self.key_generator.generate_key_pair()
        self.key_storage.store_keys(new_keys)
        self.notify_key_rotation()
```

## Безпека гаманця

### Захист приватних ключів
```python
class WalletSecurity:
    def encrypt_private_key(self, private_key: str) -> str:
        """Шифрування приватного ключа"""
        return self.encryption.encrypt_data(private_key)
        
    def decrypt_private_key(self, encrypted_key: str) -> str:
        """Розшифрування приватного ключа"""
        return self.encryption.decrypt_data(encrypted_key)
```

### Підписання транзакцій
```python
class TransactionSigner:
    def sign_transaction(self, transaction: Dict, private_key: str) -> str:
        """Підписання транзакції"""
        message = self._prepare_message(transaction)
        signature = self._sign_message(message, private_key)
        return signature
```

## Безпека API

### Rate limiting
```python
class RateLimiter:
    def check_limit(self, ip: str) -> bool:
        """Перевірка ліміту запитів"""
        current_time = time.time()
        if not self._is_within_limit(ip, current_time):
            raise RateLimitExceeded()
        return True
```

### API ключі
```python
class APIKeyManager:
    def generate_api_key(self, user_id: str) -> str:
        """Генерація API ключа"""
        key = secrets.token_urlsafe(32)
        self.store_api_key(user_id, key)
        return key
        
    def validate_api_key(self, key: str) -> bool:
        """Валідація API ключа"""
        return self.api_keys.exists(key)
```

## Аудит безпеки

### Сканування вразливостей
```python
class VulnerabilityScanner:
    def scan_system(self) -> List[Dict]:
        """Сканування системи на вразливості"""
        vulnerabilities = []
        vulnerabilities.extend(self._scan_network())
        vulnerabilities.extend(self._scan_applications())
        vulnerabilities.extend(self._scan_dependencies())
        return vulnerabilities
```

### Перевірка конфігурації
```python
class SecurityAuditor:
    def audit_configuration(self) -> Dict:
        """Аудит конфігурації безпеки"""
        return {
            "firewall": self._check_firewall(),
            "encryption": self._check_encryption(),
            "access_control": self._check_access_control(),
            "logging": self._check_logging()
        }
```

## Відновлення після інцидентів

### План відновлення
```python
class IncidentRecovery:
    def execute_recovery_plan(self, incident: Dict):
        """Виконання плану відновлення"""
        self._stop_attack()
        self._assess_damage()
        self._restore_systems()
        self._update_security()
```

### Резервне копіювання
```python
class SecurityBackup:
    def create_secure_backup(self):
        """Створення захищеної резервної копії"""
        data = self._collect_critical_data()
        encrypted_data = self.encryption.encrypt_data(data)
        self._store_backup(encrypted_data) 