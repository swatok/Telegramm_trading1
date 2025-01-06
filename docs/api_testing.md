# Тестування API

## Unit тести

### Тестування ендпоінтів

#### Тести торгових операцій
```python
class TestTradeEndpoints:
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
        data = response.json()
        assert data["success"] == True
        assert "id" in data["data"]
        
    async def test_get_trade(self, client: AsyncClient):
        """Тест отримання торгової операції"""
        trade_id = 1
        response = await client.get(f"/trades/{trade_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["data"]["id"] == trade_id
```

#### Тести гаманця
```python
class TestWalletEndpoints:
    async def test_get_balance(self, client: AsyncClient):
        """Тест отримання балансу"""
        response = await client.get("/wallet/balance")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "balance" in data["data"]
        
    async def test_withdraw(self, client: AsyncClient):
        """Тест виведення коштів"""
        response = await client.post(
            "/wallet/withdraw",
            json={
                "amount": "1.0",
                "address": "recipient123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "transaction_hash" in data["data"]
```

### Тестування валідації

#### Валідація вхідних даних
```python
class TestInputValidation:
    async def test_invalid_trade_amount(self, client: AsyncClient):
        """Тест невалідної суми торгової операції"""
        response = await client.post(
            "/trades/",
            json={
                "token_address": "token123",
                "amount": "-1.0",  # Невалідна сума
                "price": "100.0",
                "type": "buy"
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert data["success"] == False
        assert "amount" in data["error"]
        
    async def test_missing_required_fields(self, client: AsyncClient):
        """Тест відсутніх обов'язкових полів"""
        response = await client.post(
            "/trades/",
            json={
                "token_address": "token123"
                # Відсутні обов'язкові поля
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert data["success"] == False
```

### Тестування авторизації

#### Перевірка токенів
```python
class TestAuthorization:
    async def test_missing_token(self, client: AsyncClient):
        """Тест відсутнього токену"""
        response = await client.get("/wallet/balance")
        assert response.status_code == 401
        data = response.json()
        assert data["success"] == False
        assert "token" in data["error"]
        
    async def test_invalid_token(self, client: AsyncClient):
        """Тест невалідного токену"""
        response = await client.get(
            "/wallet/balance",
            headers={"Authorization": "invalid_token"}
        )
        assert response.status_code == 401
        data = response.json()
        assert data["success"] == False
```

## Інтеграційні тести

### Тестування бізнес-логіки

#### Повний цикл торгівлі
```python
class TestTradingFlow:
    async def test_complete_trade_cycle(self, client: AsyncClient):
        """Тест повного циклу торгівлі"""
        # Створення торгової операції
        trade_response = await client.post(
            "/trades/",
            json={
                "token_address": "token123",
                "amount": "1.0",
                "price": "100.0",
                "type": "buy"
            }
        )
        assert trade_response.status_code == 200
        trade_id = trade_response.json()["data"]["id"]
        
        # Перевірка статусу
        status_response = await client.get(f"/trades/{trade_id}")
        assert status_response.status_code == 200
        assert status_response.json()["data"]["status"] == "completed"
        
        # Перевірка балансу
        balance_response = await client.get("/wallet/balance")
        assert balance_response.status_code == 200
        assert float(balance_response.json()["data"]["balance"]) > 0
```

### Тестування взаємодії з зовнішніми сервісами

#### Взаємодія з блокчейном
```python
class TestBlockchainInteraction:
    async def test_blockchain_sync(self, client: AsyncClient):
        """Тест синхронізації з блокчейном"""
        # Створення транзакції
        tx_response = await client.post(
            "/wallet/withdraw",
            json={
                "amount": "1.0",
                "address": "recipient123"
            }
        )
        assert tx_response.status_code == 200
        tx_hash = tx_response.json()["data"]["transaction_hash"]
        
        # Перевірка статусу транзакції
        status_response = await client.get(f"/transactions/{tx_hash}")
        assert status_response.status_code == 200
        assert status_response.json()["data"]["status"] in ["pending", "confirmed"]
```

## Навантажувальні тести

### Тестування продуктивності

#### Паралельні запити
```python
async def test_concurrent_requests():
    """Тест паралельних запитів"""
    async with AsyncClient() as client:
        # Створення задач
        tasks = []
        for _ in range(100):
            task = asyncio.create_task(
                client.get("/wallet/balance")
            )
            tasks.append(task)
            
        # Виконання запитів
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        duration = time.time() - start_time
        
        # Аналіз результатів
        success_count = sum(1 for r in results if r.status_code == 200)
        success_rate = success_count / len(results)
        average_response_time = duration / len(results)
        
        return {
            "success_rate": success_rate,
            "average_response_time": average_response_time,
            "total_duration": duration
        }
```

### Тестування стабільності

#### Довготривале тестування
```python
class TestSystemStability:
    async def test_long_running_operation(self):
        """Тест довготривалої роботи"""
        start_time = time.time()
        end_time = start_time + 3600  # 1 година
        
        results = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "errors": []
        }
        
        async with AsyncClient() as client:
            while time.time() < end_time:
                try:
                    response = await client.get("/health")
                    results["total_requests"] += 1
                    
                    if response.status_code == 200:
                        results["successful_requests"] += 1
                    else:
                        results["failed_requests"] += 1
                        results["errors"].append(response.text)
                        
                except Exception as e:
                    results["failed_requests"] += 1
                    results["errors"].append(str(e))
                    
                await asyncio.sleep(1)
                
        return results
```

## Тестування безпеки

### Тестування аутентифікації

#### Перевірка безпеки токенів
```python
class TestSecurityMeasures:
    async def test_token_expiration(self, client: AsyncClient):
        """Тест закінчення терміну дії токену"""
        # Отримання токену
        token = await self._get_expired_token()
        
        # Спроба використання токену
        response = await client.get(
            "/wallet/balance",
            headers={"Authorization": token}
        )
        assert response.status_code == 401
        assert "expired" in response.json()["error"]
```

### Тестування авторизації

#### Перевірка прав доступу
```python
class TestAccessControl:
    async def test_unauthorized_access(self, client: AsyncClient):
        """Тест неавторизованого доступу"""
        # Спроба доступу до захищеного ресурсу
        response = await client.post(
            "/admin/settings",
            headers={"Authorization": "user_token"}
        )
        assert response.status_code == 403
        assert "permission" in response.json()["error"]
```

## Документування тестів

### Опис тест-кейсів
```python
"""
Test Case ID: TC001
Title: Create Trade Operation
Priority: High
Description: Verify that a trade operation can be created successfully

Preconditions:
- User is authenticated
- User has sufficient balance

Steps:
1. Send POST request to /trades/
2. Verify response status code
3. Verify response data structure
4. Verify trade creation in database

Expected Results:
- Status code: 200
- Success: True
- Trade ID is returned
- Trade is saved in database
"""
```

### Звіти про тестування
```python
class TestReporter:
    def generate_report(self, results: Dict) -> str:
        """Генерація звіту про тестування"""
        report = []
        report.append("API Testing Report")
        report.append("=================")
        
        # Загальна статистика
        report.append(f"Total Tests: {results['total']}")
        report.append(f"Passed: {results['passed']}")
        report.append(f"Failed: {results['failed']}")
        report.append(f"Success Rate: {results['success_rate']}%")
        
        # Деталі помилок
        if results['errors']:
            report.append("\nErrors:")
            for error in results['errors']:
                report.append(f"- {error}")
                
        return "\n".join(report)
``` 