import pytest
import base64
from unittest.mock import AsyncMock, patch, MagicMock
from api.quicknode import (
    BlockchainClient,
    APIError,
    ErrorCode,
    DEFAULT_COMMITMENT,
    DEFAULT_TIMEOUT,
    DEFAULT_COMPUTE_UNIT_PRICE
)

@pytest.fixture
def mock_endpoint_manager():
    manager = MagicMock()
    manager.get_endpoint = AsyncMock(return_value="https://test.quicknode.com")
    return manager

@pytest.fixture
def client(mock_endpoint_manager):
    return BlockchainClient(
        endpoint_manager=mock_endpoint_manager,
        ssl_context=None,
        max_retries=1,
        retry_delay=0
    )

@pytest.mark.asyncio
async def test_send_transaction_success(client):
    # Підготовка
    transaction = base64.b64encode(b"test_transaction").decode()
    expected_signature = "test_signature"
    
    with patch.object(
        client,
        '_make_request',
        AsyncMock(return_value=expected_signature)
    ) as mock_request:
        # Виконання
        signature = await client.send_transaction(transaction)
        
        # Перевірка
        assert signature == expected_signature
        mock_request.assert_called_once_with(
            method="sendTransaction",
            params=[
                transaction,
                {
                    "encoding": "base64",
                    "commitment": DEFAULT_COMMITMENT,
                    "computeUnitPrice": DEFAULT_COMPUTE_UNIT_PRICE
                }
            ]
        )

@pytest.mark.asyncio
async def test_send_transaction_invalid_input(client):
    # Перевірка порожньої транзакції
    with pytest.raises(ValueError):
        await client.send_transaction("")
        
    with pytest.raises(ValueError):
        await client.send_transaction(None)

@pytest.mark.asyncio
async def test_send_transaction_api_error(client):
    # Підготовка
    transaction = base64.b64encode(b"test_transaction").decode()
    error_message = "API Error"
    
    with patch.object(
        client,
        '_make_request',
        AsyncMock(side_effect=APIError(error_message))
    ):
        # Перевірка помилки API
        with pytest.raises(APIError) as exc_info:
            await client.send_transaction(transaction)
            
        assert str(exc_info.value) == error_message

@pytest.mark.asyncio
async def test_get_latest_blockhash_success(client):
    # Підготовка
    expected_blockhash = {
        "blockhash": "test_blockhash",
        "lastValidBlockHeight": 100
    }
    
    with patch.object(
        client,
        '_make_request',
        AsyncMock(return_value={"value": expected_blockhash})
    ) as mock_request:
        # Виконання
        blockhash = await client.get_latest_blockhash()
        
        # Перевірка
        assert blockhash == expected_blockhash
        mock_request.assert_called_once_with(
            method="getLatestBlockhash",
            params=[{"commitment": DEFAULT_COMMITMENT}]
        )

@pytest.mark.asyncio
async def test_get_latest_blockhash_api_error(client):
    # Підготовка
    error_message = "API Error"
    
    with patch.object(
        client,
        '_make_request',
        AsyncMock(side_effect=APIError(error_message))
    ):
        # Перевірка помилки API
        with pytest.raises(APIError) as exc_info:
            await client.get_latest_blockhash()
            
        assert str(exc_info.value) == error_message

@pytest.mark.asyncio
async def test_get_account_info_success(client):
    # Підготовка
    address = "test_address"
    expected_info = {
        "lamports": 1000000,
        "owner": "test_owner",
        "data": {"parsed": {"type": "account"}}
    }
    
    with patch.object(
        client,
        '_make_request',
        AsyncMock(return_value={"value": expected_info})
    ) as mock_request:
        # Виконання
        account_info = await client.get_account_info(address)
        
        # Перевірка
        assert account_info == expected_info
        mock_request.assert_called_once_with(
            method="getAccountInfo",
            params=[
                address,
                {
                    "encoding": "jsonParsed",
                    "commitment": DEFAULT_COMMITMENT
                }
            ]
        )

@pytest.mark.asyncio
async def test_get_account_info_not_found(client):
    # Підготовка
    address = "test_address"
    
    with patch.object(
        client,
        '_make_request',
        AsyncMock(return_value=None)
    ):
        # Виконання
        account_info = await client.get_account_info(address)
        
        # Перевірка
        assert account_info is None

@pytest.mark.asyncio
async def test_get_account_info_invalid_input(client):
    # Перевірка порожньої адреси
    with pytest.raises(ValueError):
        await client.get_account_info("")
        
    with pytest.raises(ValueError):
        await client.get_account_info(None)

@pytest.mark.asyncio
async def test_get_multiple_accounts_success(client):
    # Підготовка
    addresses = ["address1", "address2"]
    expected_info = {
        "value": [
            {"lamports": 1000000},
            {"lamports": 2000000}
        ]
    }
    
    with patch.object(
        client,
        '_make_request',
        AsyncMock(return_value=expected_info)
    ) as mock_request:
        # Виконання
        accounts = await client.get_multiple_accounts(addresses)
        
        # Перевірка
        assert accounts == {
            "address1": {"lamports": 1000000},
            "address2": {"lamports": 2000000}
        }
        mock_request.assert_called_once_with(
            method="getMultipleAccounts",
            params=[
                addresses,
                {
                    "encoding": "jsonParsed",
                    "commitment": DEFAULT_COMMITMENT
                }
            ]
        )

@pytest.mark.asyncio
async def test_get_multiple_accounts_invalid_input(client):
    # Перевірка порожнього списку
    with pytest.raises(ValueError):
        await client.get_multiple_accounts([])
        
    with pytest.raises(ValueError):
        await client.get_multiple_accounts(None)

@pytest.mark.asyncio
async def test_get_program_accounts_success(client):
    # Підготовка
    program_id = "test_program"
    expected_accounts = [
        {"pubkey": "account1", "account": {"data": "data1"}},
        {"pubkey": "account2", "account": {"data": "data2"}}
    ]
    
    with patch.object(
        client,
        '_make_request',
        AsyncMock(return_value=expected_accounts)
    ) as mock_request:
        # Виконання
        accounts = await client.get_program_accounts(program_id)
        
        # Перевірка
        assert accounts == expected_accounts
        mock_request.assert_called_once_with(
            method="getProgramAccounts",
            params=[
                program_id,
                {
                    "encoding": "jsonParsed",
                    "commitment": DEFAULT_COMMITMENT
                }
            ]
        )

@pytest.mark.asyncio
async def test_get_program_accounts_with_filters(client):
    # Підготовка
    program_id = "test_program"
    filters = [{"dataSize": 100}]
    data_size = 100
    
    with patch.object(
        client,
        '_make_request',
        AsyncMock(return_value=[])
    ) as mock_request:
        # Виконання
        await client.get_program_accounts(
            program_id,
            filters=filters,
            data_size=data_size
        )
        
        # Перевірка
        mock_request.assert_called_once_with(
            method="getProgramAccounts",
            params=[
                program_id,
                {
                    "encoding": "jsonParsed",
                    "commitment": DEFAULT_COMMITMENT,
                    "filters": filters,
                    "dataSize": data_size
                }
            ]
        )

@pytest.mark.asyncio
async def test_get_program_accounts_invalid_input(client):
    # Перевірка порожнього program_id
    with pytest.raises(ValueError):
        await client.get_program_accounts("")
        
    with pytest.raises(ValueError):
        await client.get_program_accounts(None) 