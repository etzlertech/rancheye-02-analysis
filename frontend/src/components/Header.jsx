import React from 'react';

const Header = () => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            <i className="fa fa-eye text-green-600"></i> RanchEye Analysis Dashboard
          </h1>
          <p className="text-gray-600">AI-powered ranch monitoring system</p>
        </div>
        <div className="text-xs text-gray-400">
          v2.0-react
        </div>
      </div>
    </div>
  );
};

export default Header;