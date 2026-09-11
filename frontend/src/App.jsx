import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import HomePage from './pages/HomePage'
import StoresPage from './pages/StoresPage'
import SearchResultsPage from './pages/SearchResultsPage'
import ShoppingListsPage from './pages/ShoppingListsPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/stores" element={<StoresPage />} />
            <Route path="/search" element={<SearchResultsPage />} />
            <Route path="/shopping-lists" element={<ShoppingListsPage />} />
          </Routes>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
