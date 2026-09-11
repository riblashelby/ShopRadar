import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { storesApi } from '../api'

const CHAIN_NAMES = {
  magnit: 'Магнит',
  pyaterochka: 'Пятёрочка',
  chizhik: 'Чижик',
  kb: 'Красное & Белое',
  custom: 'Другой',
}

export default function StoresPage() {
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    chain: 'custom',
    address: '',
    catalog_url: '',
    is_active: true,
  })

  const queryClient = useQueryClient()

  const { data: stores, isLoading } = useQuery({
    queryKey: ['stores'],
    queryFn: storesApi.list,
  })

  const { data: chains } = useQuery({
    queryKey: ['chains'],
    queryFn: storesApi.getChains,
  })

  const createMutation = useMutation({
    mutationFn: storesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries(['stores'])
      setShowForm(false)
      setFormData({ name: '', chain: 'custom', address: '', catalog_url: '', is_active: true })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: storesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries(['stores'])
    },
  })

  const toggleStoreMutation = useMutation({
    mutationFn: ({ id, is_active }) => storesApi.update(id, { is_active }),
    onSuccess: () => {
      queryClient.invalidateQueries(['stores'])
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    createMutation.mutate(formData)
  }

  // Group stores by chain
  const storesByChain = stores?.reduce((acc, store) => {
    if (!acc[store.chain]) acc[store.chain] = []
    acc[store.chain].push(store)
    return acc
  }, {}) || {}

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 pb-24">
      <header className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Мои магазины</h1>
          <p className="text-gray-600 dark:text-gray-400 text-sm mt-1">
            Добавьте магазины рядом для сравнения цен
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium"
        >
          + Добавить
        </button>
      </header>

      {/* Add Store Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 rounded-lg p-6 mb-6 shadow">
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Новый магазин</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Название *
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Например: Магнит на ул. Ленина 5"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                           bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Сеть
              </label>
              <select
                value={formData.chain}
                onChange={(e) => setFormData({ ...formData, chain: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                           bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                {chains?.chains?.map((chain) => (
                  <option key={chain.id} value={chain.id}>{chain.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Адрес
              </label>
              <input
                type="text"
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                placeholder="ул. Ленина, 5"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                           bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                URL каталога
              </label>
              <input
                type="url"
                value={formData.catalog_url}
                onChange={(e) => setFormData({ ...formData, catalog_url: e.target.value })}
                placeholder="https://..."
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                           bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>

            <div className="flex gap-2 pt-4">
              <button
                type="submit"
                disabled={createMutation.isPending}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium"
              >
                Сохранить
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 
                           text-gray-700 dark:text-gray-300 rounded-md font-medium"
              >
                Отмена
              </button>
            </div>
          </div>
        </form>
      )}

      {/* Stores List */}
      {isLoading ? (
        <div className="text-center py-8 text-gray-500">Загрузка...</div>
      ) : stores?.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg">
          <p className="text-gray-500 dark:text-gray-400 mb-4">Нет добавленных магазинов</p>
          <button
            onClick={() => setShowForm(true)}
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            Добавить первый магазин
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(storesByChain).map(([chain, chainStores]) => (
            <div key={chain}>
              <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wide">
                {CHAIN_NAMES[chain] || chain}
              </h2>
              <div className="space-y-2">
                {chainStores.map((store) => (
                  <div
                    key={store.id}
                    className={`bg-white dark:bg-gray-800 rounded-lg p-4 flex items-center justify-between
                                ${!store.is_active ? 'opacity-60' : ''}`}
                  >
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900 dark:text-white">{store.name}</h3>
                      {store.address && (
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{store.address}</p>
                      )}
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                        {store.product_count || 0} товаров
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <label className="flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={store.is_active}
                          onChange={() => toggleStoreMutation.mutate({ id: store.id, is_active: !store.is_active })}
                          className="sr-only"
                        />
                        <div className={`w-10 h-6 rounded-full transition-colors ${store.is_active ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'}`}>
                          <div className={`w-4 h-4 bg-white rounded-full transform transition-transform mt-1 ml-1 ${store.is_active ? 'translate-x-5' : ''}`} />
                        </div>
                      </label>
                      <button
                        onClick={() => deleteMutation.mutate(store.id)}
                        className="text-red-500 hover:text-red-600 p-2"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
