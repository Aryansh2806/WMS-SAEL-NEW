import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

const TransferOrders = () => {
  const { user } = useAuth();
  const [transferOrders, setTransferOrders] = useState([]);
  const [transferRequirements, setTransferRequirements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('orders');
  const [selectedTO, setSelectedTO] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedTR, setSelectedTR] = useState('');

  const backendUrl = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      
      // Fetch Transfer Orders
      const toResponse = await fetch(`${backendUrl}/api/wm/transfer-orders`, {
        credentials: 'include',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      const toData = await toResponse.json();
      setTransferOrders(toData.transfer_orders || []);

      // Fetch Transfer Requirements
      const trResponse = await fetch(`${backendUrl}/api/wm/transfer-requirements`, {
        credentials: 'include',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      const trData = await trResponse.json();
      setTransferRequirements(trData.transfer_requirements || []);

      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setLoading(false);
    }
  };

  const createTOFromTR = async () => {
    if (!selectedTR) return;

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${backendUrl}/api/wm/transfer-orders/from-tr/${selectedTR}`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        }
      });

      if (response.ok) {
        alert('Transfer Order created successfully!');
        setShowCreateModal(false);
        setSelectedTR('');
        fetchData();
      }
    } catch (error) {
      console.error('Error creating TO:', error);
      alert('Failed to create Transfer Order');
    }
  };

  const confirmTO = async (toNumber) => {
    const confirmed = window.confirm('Confirm this Transfer Order?');
    if (!confirmed) return;

    try {
      const token = localStorage.getItem('auth_token');
      
      // For simplicity, confirming with target quantities
      const to = transferOrders.find(t => t.to_number === toNumber);
      const confirmedQuantities = {};
      to.items.forEach(item => {
        confirmedQuantities[item.item_number] = item.target_quantity;
      });

      const response = await fetch(`${backendUrl}/api/wm/transfer-orders/${toNumber}/confirm`, {
        method: 'PUT',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify(confirmedQuantities)
      });

      if (response.ok) {
        alert('Transfer Order confirmed successfully!');
        fetchData();
      }
    } catch (error) {
      console.error('Error confirming TO:', error);
      alert('Failed to confirm Transfer Order');
    }
  };

  const getStatusBadge = (status) => {
    const colors = {
      OPEN: 'bg-blue-100 text-blue-800',
      IN_PROCESS: 'bg-yellow-100 text-yellow-800',
      CONFIRMED: 'bg-green-100 text-green-800',
      CANCELLED: 'bg-red-100 text-red-800'
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${colors[status] || 'bg-gray-100 text-gray-800'}`}>
        {status}
      </span>
    );
  };

  const getTypeBadge = (type) => {
    const colors = {
      PUTAWAY: 'bg-purple-100 text-purple-800',
      PICKING: 'bg-orange-100 text-orange-800',
      STOCK_TRANSFER: 'bg-teal-100 text-teal-800',
      REPLENISHMENT: 'bg-indigo-100 text-indigo-800'
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${colors[type] || 'bg-gray-100 text-gray-800'}`}>
        {type}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Transfer Orders (TO)</h1>
        <p className="text-gray-600 mt-2">Warehouse execution documents - SAP WM TO workflow</p>
      </div>

      {/* Tabs */}
      <div className="flex space-x-4 mb-6 border-b">
        <button
          onClick={() => setActiveTab('orders')}
          className={`pb-2 px-4 ${activeTab === 'orders' ? 'border-b-2 border-blue-500 text-blue-600 font-semibold' : 'text-gray-600'}`}
        >
          Transfer Orders ({transferOrders.length})
        </button>
        <button
          onClick={() => setActiveTab('requirements')}
          className={`pb-2 px-4 ${activeTab === 'requirements' ? 'border-b-2 border-blue-500 text-blue-600 font-semibold' : 'text-gray-600'}`}
        >
          Transfer Requirements ({transferRequirements.length})
        </button>
      </div>

      {/* Transfer Orders Tab */}
      {activeTab === 'orders' && (
        <div>
          <div className="mb-4 flex justify-between items-center">
            <div className="text-sm text-gray-600">
              Total Transfer Orders: {transferOrders.length}
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
              data-testid="create-to-button"
            >
              + Create TO from TR
            </button>
          </div>

          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">TO Number</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Items</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Priority</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {transferOrders.map((to) => (
                  <tr key={to.to_number} className="hover:bg-gray-50" data-testid={`to-row-${to.to_number}`}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{to.to_number}</div>
                      {to.tr_number && (
                        <div className="text-xs text-gray-500">TR: {to.tr_number}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getTypeBadge(to.to_type)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(to.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {to.items?.length || 0} items
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-900">{to.priority}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(to.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      <button
                        onClick={() => setSelectedTO(to)}
                        className="text-blue-600 hover:text-blue-900"
                        data-testid={`view-to-${to.to_number}`}
                      >
                        View
                      </button>
                      {to.status === 'OPEN' && (
                        <button
                          onClick={() => confirmTO(to.to_number)}
                          className="text-green-600 hover:text-green-900"
                          data-testid={`confirm-to-${to.to_number}`}
                        >
                          Confirm
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {transferOrders.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                No transfer orders found. Create one from a Transfer Requirement.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Transfer Requirements Tab */}
      {activeTab === 'requirements' && (
        <div>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">TR Number</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Material</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Required Qty</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Open Qty</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Priority</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {transferRequirements.map((tr) => (
                  <tr key={tr.tr_number} className="hover:bg-gray-50" data-testid={`tr-row-${tr.tr_number}`}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {tr.tr_number}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800">
                        {tr.tr_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{tr.material_code}</div>
                      <div className="text-xs text-gray-500">{tr.material_name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {tr.required_quantity} {tr.uom}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {tr.open_quantity} {tr.uom}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(tr.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {tr.priority}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {transferRequirements.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                No transfer requirements found.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Create TO Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full" data-testid="create-to-modal">
            <h3 className="text-lg font-semibold mb-4">Create Transfer Order from TR</h3>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Transfer Requirement
              </label>
              <select
                value={selectedTR}
                onChange={(e) => setSelectedTR(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
                data-testid="tr-select"
              >
                <option value="">-- Select TR --</option>
                {transferRequirements.filter(tr => tr.status === 'OPEN').map(tr => (
                  <option key={tr.tr_number} value={tr.tr_number}>
                    {tr.tr_number} - {tr.material_code} ({tr.required_quantity} {tr.uom})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex space-x-2">
              <button
                onClick={createTOFromTR}
                disabled={!selectedTR}
                className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-300"
                data-testid="confirm-create-to"
              >
                Create TO
              </button>
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setSelectedTR('');
                }}
                className="flex-1 bg-gray-200 text-gray-800 px-4 py-2 rounded-lg hover:bg-gray-300"
                data-testid="cancel-create-to"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* TO Details Modal */}
      {selectedTO && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-screen overflow-y-auto" data-testid="to-details-modal">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-xl font-semibold">{selectedTO.to_number}</h3>
                <p className="text-gray-600">Transfer Order Details</p>
              </div>
              <button
                onClick={() => setSelectedTO(null)}
                className="text-gray-500 hover:text-gray-700"
                data-testid="close-to-details"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <label className="text-sm font-medium text-gray-500">Type</label>
                <div>{getTypeBadge(selectedTO.to_type)}</div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Status</label>
                <div>{getStatusBadge(selectedTO.status)}</div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Warehouse</label>
                <div className="text-sm">{selectedTO.warehouse_number}</div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Priority</label>
                <div className="text-sm">{selectedTO.priority}</div>
              </div>
            </div>

            <h4 className="font-semibold mb-2">Items</h4>
            <table className="min-w-full divide-y divide-gray-200 mb-4">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Material</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Target Qty</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Confirmed Qty</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Destination Bin</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {selectedTO.items?.map((item, idx) => (
                  <tr key={idx}>
                    <td className="px-4 py-2 text-sm">{item.material_code}</td>
                    <td className="px-4 py-2 text-sm">{item.target_quantity} {item.uom}</td>
                    <td className="px-4 py-2 text-sm">{item.confirmed_quantity} {item.uom}</td>
                    <td className="px-4 py-2 text-sm">{item.destination_bin_code}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <button
              onClick={() => setSelectedTO(null)}
              className="w-full bg-gray-200 text-gray-800 px-4 py-2 rounded-lg hover:bg-gray-300"
              data-testid="close-to-details-button"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default TransferOrders;
