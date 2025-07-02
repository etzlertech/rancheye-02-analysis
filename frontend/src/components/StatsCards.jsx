import React from 'react';
import { useWebSocket } from '../contexts/WebSocketContext';

const StatsCards = () => {
  const { stats } = useWebSocket();

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
      {/* Today's Analyses Card */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-500 text-sm">Today's Analyses</p>
            <p className="text-2xl font-bold">
              {stats.analyses_today}
            </p>
          </div>
          <i className="fa fa-chart-line text-blue-500 text-2xl"></i>
        </div>
      </div>

      {/* Total Costs Card */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-between">
          <div className="w-full">
            <p className="text-gray-500 text-sm mb-2">Total Costs</p>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div>
                <p className="text-xs text-gray-600">Today</p>
                <p className="text-lg font-bold text-green-600">
                  ${(stats.cost_today || 0).toFixed(4)}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-600">This Week</p>
                <p className="text-lg font-bold text-blue-600">
                  ${(stats.cost_week || 0).toFixed(4)}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-600">All Time</p>
                <p className="text-lg font-bold text-purple-600">
                  ${(stats.cost_all_time || 0).toFixed(4)}
                </p>
              </div>
            </div>
          </div>
          <i className="fa fa-dollar text-purple-500 text-2xl ml-4"></i>
        </div>
      </div>
    </div>
  );
};

export default StatsCards;