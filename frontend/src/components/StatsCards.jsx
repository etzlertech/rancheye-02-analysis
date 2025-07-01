import React from 'react';
import { useWebSocket } from '../contexts/WebSocketContext';

const StatsCards = () => {
  const { stats } = useWebSocket();

  const cards = [
    {
      title: "Today's Analyses",
      value: stats.analyses_today,
      icon: 'fa-chart-line',
      color: 'text-blue-500',
    },
    {
      title: 'Cost Today',
      value: `$${stats.cost_today.toFixed(2)}`,
      icon: 'fa-dollar',
      color: 'text-purple-500',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
      {cards.map((card, index) => (
        <div key={index} className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">{card.title}</p>
              <p className="text-2xl font-bold">
                {card.value}
              </p>
            </div>
            <i className={`fa ${card.icon} ${card.color} text-2xl`}></i>
          </div>
        </div>
      ))}
    </div>
  );
};

export default StatsCards;