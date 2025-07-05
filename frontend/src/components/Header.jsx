import React from 'react';

const Header = ({ onShowHistory }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            <i className="fa fa-eye" style={{ color: '#6b7c3a' }}></i> RanchEye Analysis Dashboard
          </h1>
          <p className="text-gray-600">AI-powered ranch monitoring system</p>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={onShowHistory}
            className="px-4 py-2 bg-olive-600 text-white rounded hover:bg-olive-700 transition-colors flex items-center gap-2"
            style={{ backgroundColor: '#6b7c3a' }}
          >
            <i className="fa fa-history"></i>
            Analysis History
          </button>
          <div className="text-xs text-gray-400">
            v2.0-react
          </div>
        </div>
      </div>
    </div>
  );
};

export default Header;