import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { storesApi, searchApi } from '../api'

const QUICK_SEARCHES = [
  { query: 'кола', icon: '🥤' },
  { query: 'молоко', icon: '🥛' },
  { query: 'хлеб', icon: '🍞' },
  { query: 'яйца', icon: '🥚' },
  { query: 'курица', icon: '🍗' },
  { query: 'гречка', icon: '🌾' },
]

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState('')
  const navigate = useNavigate()

  const { data: history } = useQuery({
    queryKey: ['searchHistory'],
    queryFn: searchApi.getHistory,
  })

  const handleSearch = (query) => {
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    handleSearch(searchQuery)
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      {/* Header */}
      <header className="text-center mb-8">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
          🛒 CheapCart
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Сравнивай цены в ближайших магазинах
        </p>
      </header>

      {/* Search Box */}
      <form onSubmit={handleSubmit} className="mb-8">
        <div className="flex gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Что ищем? (например: кола, молоко, гречка)"
            className="flex-1 px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 
                       bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                       focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
          />
          <button
            type="submit"
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium 
                       rounded-lg transition-colors"
          >
            Найти
          </button>
        </div>
      </form>

      {/* Quick Searches */}
      <div className="mb-8">
        <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">
          Быстрый поиск:
        </h2>
        <div className="flex flex-wrap gap-2">
          {QUICK_SEARCHES.map((item) => (
            <button
              key={item.query}
              onClick={() => handleSearch(item.query)}
              className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 
                         rounded-full hover:border-blue-500 dark:hover:border-blue-400 
                         transition-colors text-gray-700 dark:text-gray-300"
            >
              {item.icon} {item.query}
            </button>
          ))}
        </div>
      </div>

      {/* Recent Searches */}
      {history && history.length > 0 && (
        <div>
          <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">
            Недавние запросы:
          </h2>
          <div className="flex flex-wrap gap-2">
            {history.slice(0, 5).map((item) => (
              <button
                key={item.id}
                onClick={() => handleSearch(item.query)}
                className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-800 
                           rounded-md hover:bg-gray-200 dark:hover:bg-gray-700 
                           transition-colors text-gray-700 dark:text-gray-300"
              >
                {item.query}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 py-3 px-4">
        <div className="max-w-2xl mx-auto flex justify-around">
          <button
            onClick={() => navigate('/')}
            className="flex flex-col items-center text-blue-600 dark:text-blue-400"
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
