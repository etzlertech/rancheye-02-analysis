import React from 'react';
import { formatDistanceToNow } from 'date-fns';

const ActiveAlerts = ({ alerts, loading, onAcknowledge }) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-bold mb-4 text-red-600">Active Alerts</h2>
        <div className="text-center py-4 text-gray-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-xl font-bold mb-4 text-red-600">
        Active Alerts
        {alerts.length > 0 && (
          <span className="ml-2 bg-red-100 text-red-800 px-2 py-1 rounded-full text-sm">
            {alerts.length}
          </span>
        )}
      </h2>
      
      <div className="space-y-3">
        {alerts.length === 0 ? (
          <div className="text-center py-4 text-gray-500">
            No active alerts
          </div>
        ) : (
          alerts.map((alert) => (
            <div key={alert.id} className="bg-red-50 border border-red-200 rounded-lg p-3">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="font-semibold text-red-800">{alert.alert_type}</h3>
                  <p className="text-sm text-gray-700">{alert.message}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {alert.camera_name} • {formatDistanceToNow(new Date(alert.created_at), { addSuffix: true })}
                  </p>
                </div>
                <button
                  onClick={() => onAcknowledge(alert.id)}
                  className="ml-2 bg-red-600 hover:bg-red-700 text-white px-2 py-1 rounded text-xs"
                >
                  Acknowledge
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ActiveAlerts;