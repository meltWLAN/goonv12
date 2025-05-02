# Enhanced China Stock Provider

This module has been updated to use the TushareAPIManager class for improved API handling.
Key enhancements:

1. Better caching of API requests
2. Improved error handling
3. Rate limiting to prevent API throttling
4. More efficient handling of token authentication

To use the enhanced provider, simply initialize it with your Tushare token:

```python
from china_stock_provider import ChinaStockProvider

provider = ChinaStockProvider(tushare_token='your_token_here')
data = provider.get_data('daily', '000001.SZ')
```

The provider will automatically use the TushareAPIManager for API requests
while maintaining compatibility with existing code.
