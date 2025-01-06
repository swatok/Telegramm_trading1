# Розробка API

## Структура API

### Основні ендпоінти

#### Торгові операції
```python
@router.post("/trades/")
async def create_trade(trade: TradeCreate):
    """
    Створення нової торгової операції.
    
    Args:
        trade (TradeCreate): Параметри торгової операції
        
    Returns:
        Dict: Створена торгова операція
    """
    return await trade_service.create_trade(trade)

@router.get("/trades/{trade_id}")
async def get_trade(trade_id: int):
    """
    Отримання інформації про торгову операцію.
    
    Args:
        trade_id (int): ID торгової операції
        
    Returns:
        Dict: Інформація про торгову операцію
    """
    return await trade_service.get_trade(trade_id)
```

#### Управління гаманцем
```python
@router.get("/wallet/balance")
async def get_balance():
    """
    Отримання балансу гаманця.
    
    Returns:
        Dict: Баланси по всіх токенах
    """
    return await wallet_service.get_balance()

@router.post("/wallet/withdraw")
async def withdraw(withdrawal: WithdrawalCreate):
    """
    Виведення коштів.
    
    Args:
        withdrawal (WithdrawalCreate): Параметри виведення
        
    Returns:
        Dict: Результат операції
    """
    return await wallet_service.withdraw(withdrawal)
```

## Моделі даних

### Pydantic моделі
```python
class TradeCreate(BaseModel):
    """Модель створення торгової операції"""
    token_address: str
    amount: Decimal
    price: Decimal
    type: Literal["buy", "sell"]
    
    class Config:
        json_encoders = {
            Decimal: str
        }

class Trade(TradeCreate):
    """Модель торгової операції"""
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
```

### Відповіді API
```python
class APIResponse(BaseModel):
    """Базова модель відповіді API"""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None

class PaginatedResponse(BaseModel):
    """Модель пагінованої відповіді"""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
```

## Валідація та обробка помилок

### Валідатори
```python
class TradeValidator:
    """Валідація торгових операцій"""
    
    async def validate_trade(self, trade: TradeCreate) -> bool:
        """
        Валідація торгової операції.
        
        Args:
            trade: Параметри торгової операції
            
        Raises:
            ValidationError: Помилка валідації
        """
        if not await self._check_token(trade.token_address):
            raise ValidationError("Invalid token address")
            
        if not await self._check_amount(trade.amount):
            raise ValidationError("Invalid amount")
            
        return True
```

### Обробники помилок
```python
@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Обробник помилок валідації"""
    return JSONResponse(
        status_code=400,
        content={"success": False, "error": str(exc)}
    )

@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
    """Обробник HTTP помилок"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail}
    )
```

## Middleware

### Аутентифікація
```python
@app.middleware("http")
async def authenticate(request: Request, call_next):
    """Middleware аутентифікації"""
    token = request.headers.get("Authorization")
    
    if not token:
        return JSONResponse(
            status_code=401,
            content={"success": False, "error": "Missing token"}
        )
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        request.state.user = payload
    except JWTError:
        return JSONResponse(
            status_code=401,
            content={"success": False, "error": "Invalid token"}
        )
        
    return await call_next(request)
```

### Логування
```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware логування запитів"""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    logger.info(
        f"Method: {request.method} "
        f"Path: {request.url.path} "
        f"Duration: {duration:.2f}s "
        f"Status: {response.status_code}"
    )
    
    return response
```

## Документація API

### OpenAPI специфікація
```python
app = FastAPI(
    title="Trading Bot API",
    description="API для управління торговим ботом",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Додаткова інформація
app.openapi_tags = [
    {
        "name": "trades",
        "description": "Операції з торгами"
    },
    {
        "name": "wallet",
        "description": "Операції з гаманцем"
    }
]
```

### Swagger UI налаштування
```python
app.swagger_ui_parameters = {
    "defaultModelsExpandDepth": -1,
    "docExpansion": "none",
    "filter": True
}
```

## Тестування API

### Інтеграційні тести
```python
class TestTradeAPI:
    async def test_create_trade(self, client: AsyncClient):
        """Тест створення торгової операції"""
        response = await client.post(
            "/trades/",
            json={
                "token_address": "token123",
                "amount": "1.0",
                "price": "100.0",
                "type": "buy"
            }
        )
        assert response.status_code == 200
        assert response.json()["success"] == True
```

### Навантажувальні тести
```python
async def test_api_load():
    """Навантажувальне тестування API"""
    async with AsyncClient() as client:
        tasks = []
        for _ in range(100):
            task = asyncio.create_task(
                client.get("/wallet/balance")
            )
            tasks.append(task)
            
        results = await asyncio.gather(*tasks)
        success = sum(1 for r in results if r.status_code == 200)
        return success / len(results)
```

## Безпека API

### Rate limiting
```python
class RateLimiter:
    """Обмеження кількості запитів"""
    
    async def check_limit(self, ip: str) -> bool:
        """Перевірка ліміту запитів"""
        key = f"ratelimit:{ip}"
        count = await redis.incr(key)
        
        if count == 1:
            await redis.expire(key, 60)
            
        return count <= 100
```

### API ключі
```python
class APIKeyAuth:
    """Аутентифікація по API ключу"""
    
    async def authenticate(self, api_key: str) -> bool:
        """Перевірка API ключа"""
        if not api_key:
            return False
            
        return await self._validate_key(api_key)
```

## Версіонування API

### Управління версіями
```python
class APIVersionManager:
    """Управління версіями API"""
    
    def get_version(self, request: Request) -> str:
        """Отримання версії API"""
        return request.headers.get("API-Version", "1.0")
        
    def is_deprecated(self, version: str) -> bool:
        """Перевірка застарілої версії"""
        return version < "1.0"
```

### Маршрутизація версій
```python
@router.get("/v1/trades/")
async def get_trades_v1():
    """API v1: Отримання торгових операцій"""
    return await trade_service.get_trades_v1()

@router.get("/v2/trades/")
async def get_trades_v2():
    """API v2: Отримання торгових операцій"""
    return await trade_service.get_trades_v2()
``` 