import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

const WMReports = () => {
  const { user } = useAuth();
  const [selectedReport, setSelectedReport] = useState('');
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    storage_type: '',
    stock_category: '',
    material_code: '',
    expired_only: false,
    zone: '',
    days_threshold: 30
  });

  const backendUrl = process.env.REACT_APP_BACKEND_URL;

  const reports = [
    { id: 'quant-list', name: 'LX03 - Quant List', description: 'Stock per bin with filters' },
    { id: 'bin-status', name: 'LX02 - Bin Status', description: 'Bin utilization analysis' },
    { id: 'stock-by-category', name: 'Stock by Category', description: 'UNRES/QINSP/BLOCK/RETRN breakdown' },
    { id: 'expiry-alert', name: 'SLED Expiry Alert', description: 'Expired & expiring items' },
    { id: 'transfer-order-list', name: 'LT21 - Transfer Order List', description: 'All TOs with status' },
    { id: 'stock-movement-history', name: 'Stock Movement History', description: 'Complete movement log' },
    { id: 'storage-optimization', name: 'Storage Optimization', description: 'AI-powered recommendations' }
  ];

  const generateReport = async () => {
    if (!selectedReport) return;

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      let url = `${backendUrl}/api/wm/reports/${selectedReport}`;
      
      // Add filters based on report type
      const params = new URLSearchParams();
      if (selectedReport === 'quant-list') {
        if (filters.storage_type) params.append('storage_type', filters.storage_type);
        if (filters.stock_category) params.append('stock_category', filters.stock_category);
        if (filters.material_code) params.append('material_code', filters.material_code);
        if (filters.expired_only) params.append('expired_only', 'true');
      } else if (selectedReport === 'bin-status' && filters.zone) {
        params.append('zone', filters.zone);
      } else if (selectedReport === 'expiry-alert') {
        params.append('days_threshold', filters.days_threshold);
      }

      if (params.toString()) {
        url += `?${params.toString()}`;
      }

      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      const data = await response.json();
      setReportData(data);
    } catch (error) {
      console.error('Error generating report:', error);
      alert('Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  const exportToExcel = () => {
    // Simple CSV export
    if (!reportData) return;

    let csvContent = '';
    
    if (selectedReport === 'quant-list' && reportData.quants) {
      csvContent = 'Material Code,Bin Code,Quantity,UOM,Stock Category,Batch,SLED\n';
      reportData.quants.forEach(q => {
        csvContent += `${q.material_code},${q.bin_code},${q.quantity},${q.uom},${q.stock_category},${q.batch_number || ''},${q.shelf_life_expiry_date || ''}\n`;
      });
    } else if (selectedReport === 'bin-status' && reportData.bins) {
      csvContent = 'Bin Code,Zone,Status,Capacity,Current Stock,Utilization %\n';
      reportData.bins.forEach(b => {
        csvContent += `${b.bin_code},${b.zone},${b.status},${b.capacity},${b.current_stock},${b.utilization_pct}\n`;
      });
    }

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${selectedReport}_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  const renderReportData = () => {
    if (!reportData) return null;

    // Quant List Report
    if (selectedReport === 'quant-list') {
      return (
        <div>
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Total Quants</div>
              <div className="text-2xl font-bold text-blue-600">{reportData.total_quants}</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Total Quantity</div>
              <div className="text-2xl font-bold text-green-600">{reportData.total_quantity?.toLocaleString()}</div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Unrestricted</div>
              <div className="text-2xl font-bold text-purple-600">{reportData.by_category?.UNRES?.quantity?.toLocaleString() || 0}</div>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Quality Inspection</div>
              <div className="text-2xl font-bold text-orange-600">{reportData.by_category?.QINSP?.quantity?.toLocaleString() || 0}</div>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 bg-white rounded-lg shadow">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Material</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Bin</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Batch</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">SLED</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {reportData.quants?.map((quant, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm">{quant.material_code}</td>
                    <td className="px-4 py-3 text-sm">{quant.bin_code}</td>
                    <td className="px-4 py-3 text-sm font-semibold">{quant.quantity} {quant.uom}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        quant.stock_category === 'UNRES' ? 'bg-green-100 text-green-800' :
                        quant.stock_category === 'QINSP' ? 'bg-yellow-100 text-yellow-800' :
                        quant.stock_category === 'BLOCK' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {quant.stock_category}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{quant.batch_number || '-'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{quant.shelf_life_expiry_date || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      );
    }

    // Bin Status Report
    if (selectedReport === 'bin-status') {
      return (
        <div>
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Total Bins</div>
              <div className="text-2xl font-bold text-blue-600">{reportData.summary?.total_bins}</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Occupied Bins</div>
              <div className="text-2xl font-bold text-green-600">{reportData.summary?.occupied_bins}</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Empty Bins</div>
              <div className="text-2xl font-bold text-gray-600">{reportData.summary?.empty_bins}</div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Avg Utilization</div>
              <div className="text-2xl font-bold text-purple-600">{reportData.summary?.avg_utilization?.toFixed(1)}%</div>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 bg-white rounded-lg shadow">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Bin Code</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Zone</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Capacity</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Current Stock</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Utilization</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Materials</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {reportData.bins?.map((bin, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-semibold">{bin.bin_code}</td>
                    <td className="px-4 py-3 text-sm">{bin.zone}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        bin.status === 'empty' ? 'bg-gray-100 text-gray-800' :
                        bin.status === 'available' ? 'bg-green-100 text-green-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {bin.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">{bin.capacity}</td>
                    <td className="px-4 py-3 text-sm font-semibold">{bin.current_stock}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center">
                        <div className="w-full bg-gray-200 rounded-full h-2 mr-2">
                          <div className={`h-2 rounded-full ${
                            bin.utilization_pct > 80 ? 'bg-red-500' :
                            bin.utilization_pct > 50 ? 'bg-yellow-500' :
                            'bg-green-500'
                          }`} style={{ width: `${Math.min(bin.utilization_pct, 100)}%` }}></div>
                        </div>
                        <span className="text-sm font-semibold">{bin.utilization_pct?.toFixed(1)}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm">{bin.material_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      );
    }

    // Stock by Category Report
    if (selectedReport === 'stock-by-category') {
      return (
        <div className="space-y-6">
          {reportData.categories?.map((category, idx) => (
            <div key={idx} className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h3 className="text-lg font-semibold">{category.category_name}</h3>
                  <p className="text-sm text-gray-600">{category.material_count} materials</p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-blue-600">{category.total_quantity?.toLocaleString()}</div>
                  <div className="text-sm text-gray-600">Total Units</div>
                </div>
              </div>
              
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Material</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Bins</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Batches</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {category.materials?.map((material, midx) => (
                      <tr key={midx}>
                        <td className="px-4 py-2 text-sm font-medium">{material.material_code}</td>
                        <td className="px-4 py-2 text-sm">{material.total_quantity?.toLocaleString()}</td>
                        <td className="px-4 py-2 text-sm">{material.bins}</td>
                        <td className="px-4 py-2 text-sm">{material.batch_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      );
    }

    // Generic table view for other reports
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <pre className="text-sm overflow-auto">{JSON.stringify(reportData, null, 2)}</pre>
      </div>
    );
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">WM Reports</h1>
        <p className="text-gray-600 mt-2">SAP WM standard reports - LX/LT series</p>
      </div>

      {/* Report Selection */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="grid md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Select Report</label>
            <select
              value={selectedReport}
              onChange={(e) => setSelectedReport(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              data-testid="report-select"
            >
              <option value="">-- Select a Report --</option>
              {reports.map(report => (
                <option key={report.id} value={report.id}>
                  {report.name}
                </option>
              ))}
            </select>
            {selectedReport && (
              <p className="text-sm text-gray-600 mt-1">
                {reports.find(r => r.id === selectedReport)?.description}
              </p>
            )}
          </div>

          {/* Filters */}
          {selectedReport === 'quant-list' && (
            <div className="space-y-2">
              <input
                type="text"
                placeholder="Material Code"
                value={filters.material_code}
                onChange={(e) => setFilters({...filters, material_code: e.target.value})}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
              />
              <select
                value={filters.stock_category}
                onChange={(e) => setFilters({...filters, stock_category: e.target.value})}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
              >
                <option value="">All Categories</option>
                <option value="UNRES">Unrestricted</option>
                <option value="QINSP">Quality Inspection</option>
                <option value="BLOCK">Blocked</option>
                <option value="RETRN">Returns</option>
              </select>
            </div>
          )}
        </div>

        <div className="flex space-x-2">
          <button
            onClick={generateReport}
            disabled={!selectedReport || loading}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-300"
            data-testid="generate-report-button"
          >
            {loading ? 'Generating...' : 'Generate Report'}
          </button>
          
          {reportData && (
            <button
              onClick={exportToExcel}
              className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700"
              data-testid="export-report-button"
            >
              Export to CSV
            </button>
          )}
        </div>
      </div>

      {/* Report Data */}
      {reportData && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">{reportData.report_name}</h2>
            <p className="text-sm text-gray-600">
              Generated: {new Date(reportData.generated_at).toLocaleString()}
            </p>
          </div>
          {renderReportData()}
        </div>
      )}
    </div>
  );
};

export default WMReports;
