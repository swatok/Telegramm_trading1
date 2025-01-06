import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.quicknode import (
    BalanceChecker,
    APIError,
    ErrorCode,
    DEFAULT_COMMITMENT,
    DEFAULT_TIMEOUT
)

@pytest.fixture
def mock_endpoint_manager():
    manager = MagicMock()
    manager.get_endpoint = AsyncMock(return_value="https://test.quicknode.com")
    return manager

@pytest.fixture
def checker(mock_endpoint_manager):
    return BalanceChecker(
        endpoint_manager=mock_endpoint_manager,
        ssl_context=None,
        max_retries=1,
        retry_delay=0
    )

@pytest.mark.asyncio
async def test_get_sol_balance_success(checker):
    # Підготовка
    address = "test_address"
    lamports = 1_000_000_000  # 1 SOL
    expected_balance = 1.0
    
    with patch.object(
        checker,
        '_make_request',
        AsyncMock(return_value=lamports)
    ) as mock_request:
        # Виконання
        balance = await checker.get_sol_balance(address)
        
        # Перевірка
        assert balance == expected_balance
        mock_request.assert_called_once_with(
            method="getBalance",
            params=[
                address,
                {"commitment": DEFAULT_COMMITMENT}
            ]
        )

@pytest.mark.asyncio
async def test_get_sol_balance_invalid_input(checker):
    # Перевірка порожньої адреси
    with pytest.raises(ValueError):
        await checker.get_sol_balance("")
        
    with pytest.raises(ValueError):
        await checker.get_sol_balance(None)

@pytest.mark.asyncio
async def test_get_sol_balance_api_error(checker):
    # Підготовка
    address = "test_address"
    error_message = "API Error"
    
    with patch.object(
        checker,
        '_make_request',
        AsyncMock(side_effect=APIError(error_message))
    ):
        # Перевірка помилки API
        with pytest.raises(APIError) as exc_info:
            await checker.get_sol_balance(address)
            
        assert str(exc_info.value) == error_message

@pytest.mark.asyncio
async def test_get_token_balance_success(checker):
    # Підготовка
    address = "test_address"
    token_mint = "test_token"
    token_account = "test_token_account"
    amount = 1_000_000
    decimals = 6
    expected_balance = 1.0
    
    with patch.object(
        checker,
        '_get_token_account',
        AsyncMock(return_value=token_account)
    ), patch.object(
        checker,
        '_make_request',
        AsyncMock(return_value={
            "amount": str(amount),
            "decimals": decimals
        })
    ) as mock_request:
        # Виконання
        balance = await checker.get_token_balance(address, token_mint)
        
        # Перевірка
        assert balance == expected_balance
        mock_request.assert_called_once_with(
            method="getTokenAccountBalance",
            params=[
                token_account,
                {"commitment": DEFAULT_COMMITMENT}
            ]
        )

@pytest.mark.asyncio
async def test_get_token_balance_no_account(checker):
    # Підготовка
    address = "test_address"
    token_mint = "test_token"
    
    with patch.object(
        checker,
        '_get_token_account',
        AsyncMock(return_value=None)
    ):
        # Виконання
        balance = await checker.get_token_balance(address, token_mint)
        
        # Перевірка
        assert balance == 0.0

@pytest.mark.asyncio
async def test_get_token_balance_invalid_input(checker):
    # Перевірка порожньої адреси
    with pytest.raises(ValueError):
        await checker.get_token_balance("", "token")
        
    with pytest.raises(ValueError):
        await checker.get_token_balance(None, "token")
        
    # Перевірка порожнього токена
    with pytest.raises(ValueError):
        await checker.get_token_balance("address", "")
        
    with pytest.raises(ValueError):
        await checker.get_token_balance("address", None)

@pytest.mark.asyncio
async def test_check_sufficient_balance_success(checker):
    # Підготовка
    address = "test_address"
    required_sol = 1.0
    required_tokens = {
        "token1": 1.0,
        "token2": 2.0
    }
    
    with patch.object(
        checker,
        'get_sol_balance',
        AsyncMock(return_value=2.0)
    ), patch.object(
        checker,
        'get_token_balance',
        AsyncMock(side_effect=[1.5, 2.5])
    ):
        # Виконання
        is_sufficient = await checker.check_sufficient_balance(
            address,
            required_sol,
            required_tokens
        )
        
        # Перевірка
        assert is_sufficient is True

@pytest.mark.asyncio
async def test_check_sufficient_balance_insufficient_sol(checker):
    # Підготовка
    address = "test_address"
    required_sol = 2.0
    
    with patch.object(
        checker,
        'get_sol_balance',
        AsyncMock(return_value=1.0)
    ):
        # Виконання
        is_sufficient = await checker.check_sufficient_balance(
            address,
            required_sol
        )
        
        # Перевірка
        assert is_sufficient is False

@pytest.mark.asyncio
async def test_check_sufficient_balance_insufficient_token(checker):
    # Підготовка
    address = "test_address"
    required_sol = 1.0
    required_tokens = {
        "token1": 2.0
    }
    
    with patch.object(
        checker,
        'get_sol_balance',
        AsyncMock(return_value=1.5)
    ), patch.object(
        checker,
        'get_token_balance',
        AsyncMock(return_value=1.0)
    ):
        # Виконання
        is_sufficient = await checker.check_sufficient_balance(
            address,
            required_sol,
            required_tokens
        )
        
        # Перевірка
        assert is_sufficient is False

@pytest.mark.asyncio
async def test_check_sufficient_balance_invalid_input(checker):
    # Перевірка порожньої адреси
    with pytest.raises(ValueError):
        await checker.check_sufficient_balance("", 1.0)
        
    with pytest.raises(ValueError):
        await checker.check_sufficient_balance(None, 1.0)
        
    # Перевірка від'ємної кількості SOL
    with pytest.raises(ValueError):
        await checker.check_sufficient_balance("address", -1.0)
        
    # Перевірка від'ємної кількості токенів
    with pytest.raises(ValueError):
        await checker.check_sufficient_balance(
            "address",
            1.0,
            {"token": -1.0}
        )

@pytest.mark.asyncio
async def test_get_token_account_success(checker):
    # Підготовка
    owner = "test_owner"
    token_mint = "test_token"
    expected_account = "test_account"
    
    with patch.object(
        checker,
        '_make_request',
        AsyncMock(return_value={
            "value": [
                {
                    "pubkey": expected_account,
                    "account": {
                        "data": {
                            "parsed": {
                                "info": {
                                    "mint": token_mint
                                }
                            }
                        }
                    }
                }
            ]
        })
    ) as mock_request:
        # Виконання
        account = await checker._get_token_account(
            owner,
            token_mint,
            DEFAULT_COMMITMENT
        )
        
        # Перевірка
        assert account == expected_account

@pytest.mark.asyncio
async def test_get_token_account_not_found(checker):
    # Підготовка
    owner = "test_owner"
    token_mint = "test_token"
    
    with patch.object(
        checker,
        '_make_request',
        AsyncMock(return_value={"value": []})
    ):
        # Виконання
        account = await checker._get_token_account(
            owner,
            token_mint,
            DEFAULT_COMMITMENT
        )
        
        # Перевірка
        assert account is None 