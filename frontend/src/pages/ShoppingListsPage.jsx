import React from 'react';
import { Link } from 'react-router-dom';

const ShoppingListsPage = () => {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          Списки покупок
        </h1>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 text-center">
          <p className="text-gray-600 dark:text-gray-300 mb-4">
            Функционал списков покупок находится в разработке.
          </p>
          <Link 
            to="/" 
            className="inline-block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            Вернуться к поиску
          </Link>
        </div>
      </div>
    </div>
  );
};

export default ShoppingListsPage;
