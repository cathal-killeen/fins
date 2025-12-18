import { Wallet, TrendingUp, TrendingDown, DollarSign } from 'lucide-react'

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Dashboard</h1>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">Total Balance</span>
              <Wallet className="h-5 w-5 text-primary-500" />
            </div>
            <p className="text-2xl font-bold text-gray-900">$0.00</p>
            <p className="text-sm text-gray-500 mt-1">Across all accounts</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">This Month Income</span>
              <TrendingUp className="h-5 w-5 text-green-500" />
            </div>
            <p className="text-2xl font-bold text-gray-900">$0.00</p>
            <p className="text-sm text-green-600 mt-1">+0% from last month</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">This Month Expenses</span>
              <TrendingDown className="h-5 w-5 text-red-500" />
            </div>
            <p className="text-2xl font-bold text-gray-900">$0.00</p>
            <p className="text-sm text-red-600 mt-1">+0% from last month</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">Net Savings</span>
              <DollarSign className="h-5 w-5 text-primary-500" />
            </div>
            <p className="text-2xl font-bold text-gray-900">$0.00</p>
            <p className="text-sm text-gray-500 mt-1">This month</p>
          </div>
        </div>

        {/* Recent Transactions */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Recent Transactions</h2>
          </div>
          <div className="p-6">
            <p className="text-gray-500 text-center py-8">No transactions yet</p>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <button className="bg-white rounded-lg shadow p-6 text-left hover:shadow-md transition-shadow">
            <h3 className="font-semibold text-gray-900 mb-2">Add Transaction</h3>
            <p className="text-sm text-gray-600">Manually add a new transaction</p>
          </button>

          <button className="bg-white rounded-lg shadow p-6 text-left hover:shadow-md transition-shadow">
            <h3 className="font-semibold text-gray-900 mb-2">Import CSV</h3>
            <p className="text-sm text-gray-600">Import transactions from bank</p>
          </button>

          <button className="bg-white rounded-lg shadow p-6 text-left hover:shadow-md transition-shadow">
            <h3 className="font-semibold text-gray-900 mb-2">View Analytics</h3>
            <p className="text-sm text-gray-600">Explore spending insights</p>
          </button>
        </div>
      </div>
    </div>
  )
}
