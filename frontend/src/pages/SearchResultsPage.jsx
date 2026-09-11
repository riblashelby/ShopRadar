import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { searchApi } from '../api'

export default function SearchResultsPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const query = searchParams.get('q') || ''
  const [isSearching, setIsSearching] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (query) {
      performSearch(query)
    }
  }, [query])

  const performSearch = async (searchQuery) => {
    setIsSearching(true)
    setError(null)
    try {
      const data = await searchApi.search(searchQuery, { force_refresh: false })
      setResults(data)
    } catch (err) {
      setError(err.message || 'Ошибка при поиске')
    } finally {
      setIsSearching(false)
    }
  }

  const formatPrice = (price) => {
    return `${price.toFixed(2)} ₽`
  }

  const formatUnitPrice = (unitPrice, unit) => {
    if (!unitPrice) return '—'
    const baseUnit = unit === 'ml' || unit === 'l' ? 'л' : 'кг'
    return `${unitPrice.toFixed(2)} ₽/${baseUnit}`
  }

  if (!query) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8 text-center">
        <p className="text-gray-500 dark:text-gray-400">Введите поисковый запрос</p>
        <button
          onClick={() => navigate('/')}
          className="mt-4 text-blue-600 hover:text-blue-700"
        >
          ← На главную
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 pb-24">
      {/* Header */}
      <header className="mb-6">
        <button
          onClick={() => navigate('/')}
          className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 mb-4"
        >
          ← Назад
        </button>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Результаты: "{query}"
        </h1>
        {results && (
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Найдено {results.total_results} товаров в {results.stores_searched} магазинах
            {results.search_time_ms && ` за ${results.search_time_ms.toFixed(0)}мс`}
          </p>
        )}
      </header>

      {/* Loading State */}
      {isSearching && (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-500 dark:text-gray-400">Ищем лучшие цены...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-600 dark:text-red-400">{error}</p>
          <button
            onClick={() => performSearch(query)}
            className="mt-2 text-red-600 hover:text-red-700 font-medium"
          >
            Попробовать снова
          </button>
        </div>
      )}

      {/* Results */}
      {results && results.products.length === 0 && !isSearching && (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg">
          <p className="text-gray-500 dark:text-gray-400">Ничего не найдено</p>
          <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">
            Попробуйте другой запрос или добавьте больше магазинов
          </p>
        </div>
      )}

      {results && results.products.length > 0 && (
        <div className="space-y-3">
          {results.products.map((product, index) => (
            <div
              key={index}
              className={`bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm
                          ${product.is_best_offer ? 'ring-2 ring-green-500 bg-green-50 dark:bg-green-900/20' : ''}`}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-gray-900 dark:text-white">
                      {product.name}
                    </h3>
                    {product.is_best_offer && (
                      <span className="px-2 py-0.5 bg-green-500 text-white text-xs rounded-full">
                        Лучшая цена
                      </span>
                    )}
                  </div>
                  
                  {product.brand && (
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                      Бренд: {product.brand}
                    </p>
                  )}
                  
                  <div className="flex items-center gap-4 mt-2 text-sm">
                    <span className="text-gray-600 dark:text-gray-400">
                      {product.volume} {product.volume_unit || 'шт'}
                    </span>
                    <span className="text-gray-600 dark:text-gray-400">
                      {formatUnitPrice(product.unit_price, product.volume_unit)}
                    </span>
                  </div>
                  
                  <div className="flex items-center gap-2 mt-2">
                    <span className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-gray-600 dark:text-gray-300">
                      🏪 {product.store_name}
                    </span>
                    {product.store_address && (
                      <span className="text-xs text-gray-400 dark:text-gray-500 truncate max-w-xs">
                        {product.store_address}
                      </span>
                    )}
                  </div>
                </div>
                
                <div className="text-right ml-4">
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {formatPrice(product.price)}
                  </p>
                  {product.url && (
                    <a
                      href={product.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-blue-600 hover:text-blue-700 mt-2 inline-block"
                    >
                      В магазине →
                    </a>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 py-3 px-4">
        <div className="max-w-2xl mx-auto flex justify-around">
          <button
            onClick={() => navigate('/')}
            className="flex flex-col items-center text-gray-500 dark:text-gray-400 hover:text-blue-600"
          >
            <span className="text-xl">🏠</span>
            <span className="text-xs mt-1">Главная</span>
          </button>
          <button
            onClick={() => navigate('/stores')}
            className="flex flex-col items-center text-gray-500 dark:text-gray-400 hover:text-blue-600"
          >
            <span className="text-xl">🏪</span>
            <span className="text-xs mt-1">Магазины</span>
          </button>
          <button
            onClick={() => navigate('/shopping-lists')}
            className="flex flex-col items-center text-gray-500 dark:text-gray-400 hover:text-blue-600"
          >
            <span className="text-xl">📝</span>
            <span className="text-xs mt-1">Списки</span>
          </button>
        </div>
      </nav>
    </div>
  )
}
