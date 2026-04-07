import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'sonner';

const QualityInspection = () => {
  const { user } = useAuth();
  const [grns, setGrns] = useState([]);
  const [selectedGRN, setSelectedGRN] = useState(null);
  const [loading, setLoading] = useState(true);
  const [inspectionData, setInspectionData] = useState({});
  const [showInspectionModal, setShowInspectionModal] = useState(false);

  const backendUrl = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchPendingGRNs();
  }, []);

  const fetchPendingGRNs = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${backendUrl}/api/grn`, {
        credentials: 'include',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      const data = await response.json();
      
      // Filter GRNs that have items pending inspection
      const pendingGRNs = data.filter(grn => 
        grn.status === 'pending' || grn.status === 'partial'
      );
      
      setGrns(pendingGRNs);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching GRNs:', error);
      toast.error('Failed to fetch pending inspections');
      setLoading(false);
    }
  };

  const openInspectionModal = (grn) => {
    setSelectedGRN(grn);
    
    // Initialize inspection data for each item
    const initialData = {};
    grn.items.forEach(item => {
      initialData[item.item_id] = {
        item_id: item.item_id,
        accepted_quantity: item.accepted_quantity || 0,
        rejected_quantity: item.rejected_quantity || 0,
        quality_inspection_status: item.quality_inspection_status || 'pending',
        rejection_reason: item.rejection_reason || '',
        bin_location: item.bin_location || ''
      };
    });
    
    setInspectionData(initialData);
    setShowInspectionModal(true);
  };

  const updateInspectionData = (itemId, field, value) => {
    setInspectionData(prev => ({
      ...prev,
      [itemId]: {
        ...prev[itemId],
        [field]: value
      }
    }));
  };

  const handlePassInspection = (itemId, item) => {
    const receivedQty = item.received_quantity || item.quantity || 0;
    updateInspectionData(itemId, 'accepted_quantity', receivedQty);
    updateInspectionData(itemId, 'rejected_quantity', 0);
    updateInspectionData(itemId, 'quality_inspection_status', 'passed');
    updateInspectionData(itemId, 'rejection_reason', '');
  };

  const handleFailInspection = (itemId, item) => {
    const receivedQty = item.received_quantity || item.quantity || 0;
    updateInspectionData(itemId, 'accepted_quantity', 0);
    updateInspectionData(itemId, 'rejected_quantity', receivedQty);
    updateInspectionData(itemId, 'quality_inspection_status', 'failed');
  };

  const handlePartialInspection = (itemId) => {
    updateInspectionData(itemId, 'quality_inspection_status', 'partial');
  };

  const submitInspection = async () => {
    try {
      // Validate inspection data
      const updates = Object.values(inspectionData);
      
      for (const update of updates) {
        const item = selectedGRN.items.find(i => i.item_id === update.item_id);
        const receivedQty = item.received_quantity || item.quantity || 0;
        
        if (update.accepted_quantity + update.rejected_quantity > receivedQty) {
          toast.error(`Accepted + Rejected quantity cannot exceed received quantity for ${item.material_name}`);
          return;
        }
        
        if (update.quality_inspection_status === 'failed' && !update.rejection_reason) {
          toast.error(`Please provide rejection reason for ${item.material_name}`);
          return;
        }
      }

      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${backendUrl}/api/grn/${selectedGRN.grn_id}/inspect`, {
        method: 'PUT',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify(updates)
      });

      if (response.ok) {
        toast.success('Quality inspection updated successfully');
        setShowInspectionModal(false);
        setSelectedGRN(null);
        fetchPendingGRNs();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to update inspection');
      }
    } catch (error) {
      console.error('Error submitting inspection:', error);
      toast.error('Failed to submit inspection');
    }
  };

  const getStatusBadge = (status) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      passed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      partial: 'bg-orange-100 text-orange-800'
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${colors[status] || 'bg-gray-100 text-gray-800'}`}>
        {status.toUpperCase()}
      </span>
    );
  };

  const getStockCategoryBadge = (category) => {
    const colors = {
      UNRES: 'bg-green-100 text-green-800',
      QINSP: 'bg-yellow-100 text-yellow-800',
      BLOCK: 'bg-red-100 text-red-800',
      RETRN: 'bg-orange-100 text-orange-800'
    };
    const names = {
      UNRES: 'Unrestricted',
      QINSP: 'QC Hold',
      BLOCK: 'Blocked',
      RETRN: 'Returns'
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${colors[category] || 'bg-gray-100 text-gray-800'}`}>
        {names[category] || category}
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
        <h1 className="text-3xl font-bold text-gray-900">Quality Inspection</h1>
        <p className="text-gray-600 mt-2">Inspect incoming materials and update stock categories</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
          <div className="text-sm text-gray-600">Pending Inspection</div>
          <div className="text-2xl font-bold text-yellow-600">
            {grns.reduce((acc, grn) => acc + (grn.items?.filter(i => i.quality_inspection_status === 'pending').length || 0), 0)}
          </div>
        </div>
        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
          <div className="text-sm text-gray-600">Passed</div>
          <div className="text-2xl font-bold text-green-600">
            {grns.reduce((acc, grn) => acc + (grn.items?.filter(i => i.quality_inspection_status === 'passed').length || 0), 0)}
          </div>
        </div>
        <div className="bg-red-50 p-4 rounded-lg border border-red-200">
          <div className="text-sm text-gray-600">Failed</div>
          <div className="text-2xl font-bold text-red-600">
            {grns.reduce((acc, grn) => acc + (grn.items?.filter(i => i.quality_inspection_status === 'failed').length || 0), 0)}
          </div>
        </div>
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <div className="text-sm text-gray-600">Total GRNs</div>
          <div className="text-2xl font-bold text-blue-600">{grns.length}</div>
        </div>
      </div>

      {/* GRN List */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold">Pending Inspections</h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">GRN Number</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vendor</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Items</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {grns.map((grn) => (
                <tr key={grn.grn_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{grn.grn_number}</div>
                    <div className="text-xs text-gray-500">PO: {grn.po_number}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{grn.vendor_name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(grn.receipt_date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{grn.items?.length || 0} items</div>
                    <div className="text-xs text-gray-500">
                      {grn.items?.filter(i => i.quality_inspection_status === 'pending').length || 0} pending
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getStatusBadge(grn.status)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => openInspectionModal(grn)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      Inspect
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {grns.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No pending inspections
            </div>
          )}
        </div>
      </div>

      {/* Inspection Modal */}
      {showInspectionModal && selectedGRN && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 p-6">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-xl font-semibold">Quality Inspection</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    GRN: {selectedGRN.grn_number} | Vendor: {selectedGRN.vendor_name}
                  </p>
                </div>
                <button
                  onClick={() => setShowInspectionModal(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
              </div>
            </div>

            <div className="p-6">
              <div className="space-y-6">
                {selectedGRN.items.map((item) => {
                  const itemData = inspectionData[item.item_id] || {};
                  const receivedQty = item.received_quantity || item.quantity || 0;
                  const pendingQty = receivedQty - (itemData.accepted_quantity || 0) - (itemData.rejected_quantity || 0);

                  return (
                    <div key={item.item_id} className="border border-gray-200 rounded-lg p-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Material</label>
                          <div className="text-sm text-gray-900">{item.material_code}</div>
                          <div className="text-xs text-gray-500">{item.material_name}</div>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Batch Number</label>
                          <div className="text-sm text-gray-900">{item.batch_number || 'N/A'}</div>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                        <div className="bg-blue-50 p-3 rounded">
                          <label className="block text-xs text-gray-600">Received</label>
                          <div className="text-lg font-semibold text-blue-600">{receivedQty}</div>
                        </div>
                        <div className="bg-green-50 p-3 rounded">
                          <label className="block text-xs text-gray-600">Accepted</label>
                          <input
                            type="number"
                            min="0"
                            max={receivedQty}
                            value={itemData.accepted_quantity || 0}
                            onChange={(e) => updateInspectionData(item.item_id, 'accepted_quantity', parseInt(e.target.value) || 0)}
                            className="w-full text-lg font-semibold bg-transparent border-0 p-0 focus:ring-0"
                          />
                        </div>
                        <div className="bg-red-50 p-3 rounded">
                          <label className="block text-xs text-gray-600">Rejected</label>
                          <input
                            type="number"
                            min="0"
                            max={receivedQty}
                            value={itemData.rejected_quantity || 0}
                            onChange={(e) => updateInspectionData(item.item_id, 'rejected_quantity', parseInt(e.target.value) || 0)}
                            className="w-full text-lg font-semibold bg-transparent border-0 p-0 focus:ring-0"
                          />
                        </div>
                        <div className="bg-gray-50 p-3 rounded">
                          <label className="block text-xs text-gray-600">Pending</label>
                          <div className="text-lg font-semibold text-gray-600">{pendingQty}</div>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Bin Location</label>
                          <input
                            type="text"
                            value={itemData.bin_location || ''}
                            onChange={(e) => updateInspectionData(item.item_id, 'bin_location', e.target.value)}
                            placeholder="e.g., QC-01-01-01"
                            className="w-full border border-gray-300 rounded px-3 py-2"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                          <select
                            value={itemData.quality_inspection_status || 'pending'}
                            onChange={(e) => updateInspectionData(item.item_id, 'quality_inspection_status', e.target.value)}
                            className="w-full border border-gray-300 rounded px-3 py-2"
                          >
                            <option value="pending">Pending</option>
                            <option value="passed">Passed</option>
                            <option value="failed">Failed</option>
                            <option value="partial">Partial</option>
                          </select>
                        </div>
                      </div>

                      {(itemData.quality_inspection_status === 'failed' || itemData.rejected_quantity > 0) && (
                        <div className="mb-4">
                          <label className="block text-sm font-medium text-gray-700 mb-2">Rejection Reason</label>
                          <textarea
                            value={itemData.rejection_reason || ''}
                            onChange={(e) => updateInspectionData(item.item_id, 'rejection_reason', e.target.value)}
                            placeholder="Enter reason for rejection..."
                            rows="2"
                            className="w-full border border-gray-300 rounded px-3 py-2"
                          />
                        </div>
                      )}

                      <div className="flex gap-2">
                        <button
                          onClick={() => handlePassInspection(item.item_id, item)}
                          className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                        >
                          ✓ Pass All
                        </button>
                        <button
                          onClick={() => handleFailInspection(item.item_id, item)}
                          className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                        >
                          ✗ Reject All
                        </button>
                        <button
                          onClick={() => handlePartialInspection(item.item_id)}
                          className="px-3 py-1 bg-orange-600 text-white text-sm rounded hover:bg-orange-700"
                        >
                          ↔ Partial
                        </button>
                      </div>

                      <div className="mt-3 text-xs text-gray-500">
                        <div>Stock Category: {getStockCategoryBadge(itemData.quality_inspection_status === 'passed' ? 'UNRES' : 'QINSP')}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="sticky bottom-0 bg-white border-t border-gray-200 p-6">
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setShowInspectionModal(false)}
                  className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
                >
                  Cancel
                </button>
                <button
                  onClick={submitInspection}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Submit Inspection
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QualityInspection;
