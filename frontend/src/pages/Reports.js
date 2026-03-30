import React, { useState, useEffect } from 'react';
import { reportAPI } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from '../components/ui/dialog';
import { 
  Download, FileSpreadsheet, FileText, BarChart3, Package, MapPin, Activity, 
  Calendar, Search, Filter, RefreshCw, Clock, AlertTriangle, TrendingDown,
  Users, Printer, CheckCircle, XCircle, ArrowUpDown, ChevronRight, Layers
} from 'lucide-react';
import { toast } from 'sonner';

const REPORT_CATEGORIES = [
  {
    id: 'inventory',
    name: 'Inventory Reports',
    icon: Package,
    reports: [
      { id: 'grn-stock', name: 'GRN-wise Stock', description: 'All GRNs with received quantities' },
      { id: 'batch-stock', name: 'Batch-wise Stock', description: 'Stock by batch/lot number' },
      { id: 'bin-stock', name: 'Bin-wise Stock', description: 'Bin locations with contents' },
      { id: 'stock-summary', name: 'Stock Summary', description: 'Current stock levels' },
      { id: 'stock-reconciliation', name: 'Stock Reconciliation', description: 'System vs bin stock comparison' }
    ]
  },
  {
    id: 'movement',
    name: 'Movement Reports',
    icon: Activity,
    reports: [
      { id: 'movement-history', name: 'Movement History', description: 'All inward/outward movements' },
      { id: 'daily-summary', name: 'Daily Summary', description: 'Daily inward/outward totals' },
      { id: 'putaway-pending', name: 'Putaway Pending', description: 'Items awaiting putaway' }
    ]
  },
  {
    id: 'compliance',
    name: 'Compliance Reports',
    icon: CheckCircle,
    reports: [
      { id: 'fifo-compliance', name: 'FIFO Compliance', description: 'FIFO material issue compliance' },
      { id: 'non-fifo-exceptions', name: 'Non-FIFO Exceptions', description: 'Cases where FIFO was bypassed' }
    ]
  },
  {
    id: 'aging',
    name: 'Stock Analysis',
    icon: TrendingDown,
    reports: [
      { id: 'stock-aging', name: 'Stock Aging', description: 'Stock by age category' },
      { id: 'dead-slow-stock', name: 'Dead/Slow Stock', description: 'Materials with no recent movement' }
    ]
  },
  {
    id: 'audit',
    name: 'Audit & Activity',
    icon: Users,
    reports: [
      { id: 'user-activity', name: 'User Activity Log', description: 'User actions audit trail' },
      { id: 'reprint-log', name: 'Reprint Sticker Log', description: 'Label reprint history' }
    ]
  }
];

const Reports = () => {
  const { hasPermission } = useAuth();
  const [selectedCategory, setSelectedCategory] = useState('inventory');
  const [selectedReport, setSelectedReport] = useState('grn-stock');
  const [data, setData] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [isDownloadDialogOpen, setIsDownloadDialogOpen] = useState(false);
  
  // Filters
  const [filters, setFilters] = useState({
    start_date: '',
    end_date: '',
    material_code: '',
    batch_number: '',
    bin_code: '',
    zone: '',
    vendor: ''
  });

  // All available reports for download selection
  const allReports = REPORT_CATEGORIES.flatMap(cat => 
    cat.id === 'audit' && !hasPermission(['Admin', 'Auditor', 'Store In-Charge']) 
      ? [] 
      : cat.reports.map(r => ({ ...r, category: cat.name }))
  );

  const canViewAuditReports = hasPermission(['Admin', 'Auditor', 'Store In-Charge']);

  useEffect(() => {
    loadReport();
  }, [selectedReport]);

  const loadReport = async () => {
    setLoading(true);
    try {
      let response;
      const params = Object.fromEntries(
        Object.entries(filters).filter(([_, v]) => v !== '')
      );
      
      switch (selectedReport) {
        case 'grn-stock':
          response = await reportAPI.grnStock(params);
          break;
        case 'batch-stock':
          response = await reportAPI.batchStock(params);
          break;
        case 'bin-stock':
          response = await reportAPI.binStock(params);
          break;
        case 'movement-history':
          response = await reportAPI.movementHistory(params);
          break;
        case 'fifo-compliance':
          response = await reportAPI.fifoCompliance(params);
          break;
        case 'non-fifo-exceptions':
          response = await reportAPI.nonFifoExceptions(params);
          break;
        case 'putaway-pending':
          response = await reportAPI.putawayPending(params);
          break;
        case 'stock-aging':
          response = await reportAPI.stockAging(params);
          break;
        case 'dead-slow-stock':
          response = await reportAPI.deadSlowStock(params);
          break;
        case 'daily-summary':
          response = await reportAPI.dailySummary(params);
          break;
        case 'user-activity':
          if (!canViewAuditReports) {
            toast.error('Insufficient permissions');
            return;
          }
          response = await reportAPI.userActivity(params);
          break;
        case 'reprint-log':
          if (!canViewAuditReports) {
            toast.error('Insufficient permissions');
            return;
          }
          response = await reportAPI.reprintLog(params);
          break;
        case 'stock-reconciliation':
          response = await reportAPI.stockReconciliation(params);
          break;
        case 'stock-summary':
          response = await reportAPI.stockSummary(params);
          break;
        default:
          response = { data: { data: [], total: 0 } };
      }
      
      setData(response.data.data || []);
      setTotal(response.data.total || 0);
    } catch (error) {
      console.error('Failed to load report:', error);
      toast.error('Failed to load report');
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    const params = Object.fromEntries(
      Object.entries(filters).filter(([_, v]) => v !== '')
    );
    
    try {
      setExporting(true);
      const token = localStorage.getItem('auth_token');
      const queryParams = new URLSearchParams({ 
        report_type: selectedReport, 
        ...params,
        ...(token && { token })
      });
      
      const url = `${process.env.REACT_APP_BACKEND_URL}/api/reports/export/${format === 'excel' ? 'excel' : 'pdf'}?${queryParams.toString()}`;
      
      // Use fetch with credentials to include cookies
      const response = await fetch(url, {
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error('Download failed');
      }
      
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `${selectedReport}-${new Date().toISOString().slice(0,10)}.${format === 'excel' ? 'xlsx' : 'pdf'}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
      
      toast.success(`Downloaded ${currentReport?.name || selectedReport} as ${format.toUpperCase()}`);
    } catch (error) {
      console.error('Download error:', error);
      toast.error('Failed to download report');
    } finally {
      setExporting(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const applyFilters = () => {
    loadReport();
  };

  const clearFilters = () => {
    setFilters({
      start_date: '',
      end_date: '',
      material_code: '',
      batch_number: '',
      bin_code: '',
      zone: '',
      vendor: ''
    });
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      'completed': 'bg-green-100 text-green-700',
      'pending': 'bg-amber-100 text-amber-700',
      'partial': 'bg-blue-100 text-blue-700',
      'cancelled': 'bg-red-100 text-red-700',
      'Match': 'bg-green-100 text-green-700',
      'Excess': 'bg-blue-100 text-blue-700',
      'Shortage': 'bg-red-100 text-red-700',
      'Compliant': 'bg-green-100 text-green-700',
      'Dead Stock': 'bg-red-100 text-red-700',
      'Slow Moving': 'bg-amber-100 text-amber-700',
      'available': 'bg-green-100 text-green-700',
      'blocked': 'bg-red-100 text-red-700',
      'empty': 'bg-gray-100 text-gray-700'
    };
    return statusMap[status] || 'bg-gray-100 text-gray-700';
  };

  const renderTable = () => {
    if (loading) {
      return (
        <div className="p-12 text-center text-gray-500">
          <RefreshCw className="w-8 h-8 mx-auto mb-3 animate-spin opacity-50" />
          <p>Loading report data...</p>
        </div>
      );
    }

    if (data.length === 0) {
      return (
        <div className="p-12 text-center text-gray-500">
          <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-20" />
          <p className="text-lg font-medium">No data available</p>
          <p className="text-sm">Try adjusting your filters</p>
        </div>
      );
    }

    // Render different tables based on report type
    switch (selectedReport) {
      case 'grn-stock':
        return (
          <Table>
            <TableHeader>
              <TableRow className="bg-gray-50">
                <TableHead className="font-semibold">GRN Number</TableHead>
                <TableHead className="font-semibold">Vendor</TableHead>
                <TableHead className="font-semibold">PO Number</TableHead>
                <TableHead className="font-semibold">Invoice</TableHead>
                <TableHead className="font-semibold text-right">Received</TableHead>
                <TableHead className="font-semibold text-right">Accepted</TableHead>
                <TableHead className="font-semibold text-right">Rejected</TableHead>
                <TableHead className="font-semibold">Status</TableHead>
                <TableHead className="font-semibold">Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((item, idx) => (
                <TableRow key={idx} className="hover:bg-gray-50">
                  <TableCell className="font-mono font-medium">{item.grn_number}</TableCell>
                  <TableCell>{item.vendor_name}</TableCell>
                  <TableCell>{item.po_number || '-'}</TableCell>
                  <TableCell>{item.invoice_number || '-'}</TableCell>
                  <TableCell className="text-right tabular-nums">{item.total_received_quantity || 0}</TableCell>
                  <TableCell className="text-right tabular-nums text-green-600">{item.total_accepted_quantity || 0}</TableCell>
                  <TableCell className="text-right tabular-nums text-red-600">{item.total_rejected_quantity || 0}</TableCell>
                  <TableCell><Badge className={getStatusBadge(item.status)}>{item.status}</Badge></TableCell>
                  <TableCell className="text-sm text-gray-600">{item.created_at?.slice(0, 10)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        );

      case 'batch-stock':
        return (
          <Table>
            <TableHeader>
              <TableRow className="bg-gray-50">
                <TableHead className="font-semibold">GRN #</TableHead>
                <TableHead className="font-semibold">Material</TableHead>
                <TableHead className="font-semibold">Batch/Lot</TableHead>
                <TableHead className="font-semibold text-right">Quantity</TableHead>
                <TableHead className="font-semibold">Mfg Date</TableHead>
                <TableHead className="font-semibold">Expiry</TableHead>
                <TableHead className="font-semibold">Storage</TableHead>
                <TableHead className="font-semibold">Bin</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((item, idx) => (
                <TableRow key={idx} className="hover:bg-gray-50">
                  <TableCell className="font-mono text-sm">{item.grn_number}</TableCell>
                  <TableCell>
                    <div>
                      <p className="font-mono font-medium">{item.material_code}</p>
                      <p className="text-sm text-gray-500">{item.material_name}</p>
                    </div>
                  </TableCell>
                  <TableCell className="font-mono">{item.batch_number}</TableCell>
                  <TableCell className="text-right tabular-nums font-medium">{item.accepted_quantity}</TableCell>
                  <TableCell>{item.manufacturing_date?.slice(0, 10) || '-'}</TableCell>
                  <TableCell>{item.expiry_date?.slice(0, 10) || '-'}</TableCell>
                  <TableCell className="capitalize">{item.storage_condition || '-'}</TableCell>
                  <TableCell className="font-mono">{item.bin_location || '-'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        );

      case 'bin-stock':
        return (
          <Table>
            <TableHeader>
              <TableRow className="bg-gray-50">
                <TableHead className="font-semibold">Bin Code</TableHead>
                <TableHead className="font-semibold">Zone</TableHead>
                <TableHead className="font-semibold">Location</TableHead>
                <TableHead className="font-semibold">Material</TableHead>
                <TableHead className="font-semibold text-right">Capacity</TableHead>
                <TableHead className="font-semibold text-right">Stock</TableHead>
                <TableHead className="font-semibold">Utilization</TableHead>
                <TableHead className="font-semibold">Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((item, idx) => {
                const util = item.utilization_percent || 0;
                let utilColor = 'bg-green-500';
                if (util > 90) utilColor = 'bg-red-500';
                else if (util > 70) utilColor = 'bg-amber-500';
                
                return (
                  <TableRow key={idx} className="hover:bg-gray-50">
                    <TableCell className="font-mono font-medium">{item.bin_code}</TableCell>
                    <TableCell>Zone {item.zone}</TableCell>
                    <TableCell className="text-sm text-gray-600">A{item.aisle} R{item.rack} L{item.level}</TableCell>
                    <TableCell className="font-mono">{item.material_code || '-'}</TableCell>
                    <TableCell className="text-right tabular-nums">{item.capacity}</TableCell>
                    <TableCell className="text-right tabular-nums font-medium">{item.current_stock}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div className={`h-full ${utilColor}`} style={{ width: `${util}%` }} />
                        </div>
                        <span className="text-xs tabular-nums">{util}%</span>
                      </div>
                    </TableCell>
                    <TableCell><Badge className={getStatusBadge(item.status)}>{item.status}</Badge></TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        );

      case 'movement-history':
        return (
          <Table>
            <TableHeader>
              <TableRow className="bg-gray-50">
                <TableHead className="font-semibold">Type</TableHead>
                <TableHead className="font-semibold">Material</TableHead>
                <TableHead className="font-semibold text-right">Quantity</TableHead>
                <TableHead className="font-semibold">From Bin</TableHead>
                <TableHead className="font-semibold">To Bin</TableHead>
                <TableHead className="font-semibold">Batch</TableHead>
                <TableHead className="font-semibold">Reference</TableHead>
                <TableHead className="font-semibold">Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((item, idx) => (
                <TableRow key={idx} className="hover:bg-gray-50">
                  <TableCell>
                    <Badge className={
                      item.movement_type === 'inward' ? 'bg-green-100 text-green-700' :
                      item.movement_type === 'outward' ? 'bg-red-100 text-red-700' :
                      'bg-blue-100 text-blue-700'
                    }>{item.movement_type}</Badge>
                  </TableCell>
                  <TableCell className="font-mono font-medium">{item.material_code}</TableCell>
                  <TableCell className="text-right tabular-nums font-medium">{item.quantity}</TableCell>
                  <TableCell className="font-mono">{item.from_bin || '-'}</TableCell>
                  <TableCell className="font-mono">{item.to_bin || '-'}</TableCell>
                  <TableCell className="font-mono text-sm">{item.batch_number || '-'}</TableCell>
                  <TableCell className="text-sm text-gray-600">{item.reference_type || '-'}</TableCell>
                  <TableCell className="text-sm">{item.created_at?.slice(0, 16).replace('T', ' ')}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        );

      case 'stock-aging':
        return (
          <Table>
            <TableHeader>
              <TableRow className="bg-gray-50">
                <TableHead className="font-semibold">Material</TableHead>
                <TableHead className="font-semibold">Batch</TableHead>
                <TableHead className="font-semibold text-right">Quantity</TableHead>
                <TableHead className="font-semibold">Receipt Date</TableHead>
                <TableHead className="font-semibold text-right">Age (Days)</TableHead>
                <TableHead className="font-semibold">Age Bucket</TableHead>
                <TableHead className="font-semibold">Expiry</TableHead>
                <TableHead className="font-semibold">Bin</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((item, idx) => (
                <TableRow key={idx} className="hover:bg-gray-50">
                  <TableCell>
                    <div>
                      <p className="font-mono font-medium">{item.material_code}</p>
                      <p className="text-sm text-gray-500">{item.material_name}</p>
                    </div>
                  </TableCell>
                  <TableCell className="font-mono">{item.batch_number}</TableCell>
                  <TableCell className="text-right tabular-nums font-medium">{item.quantity}</TableCell>
                  <TableCell>{item.receipt_date?.slice(0, 10)}</TableCell>
                  <TableCell className="text-right tabular-nums">{item.age_days}</TableCell>
                  <TableCell>
                    <Badge className={
                      item.aging_bucket === '0-30 days' ? 'bg-green-100 text-green-700' :
                      item.aging_bucket === '31-60 days' ? 'bg-blue-100 text-blue-700' :
                      item.aging_bucket === '61-90 days' ? 'bg-amber-100 text-amber-700' :
                      'bg-red-100 text-red-700'
                    }>{item.aging_bucket}</Badge>
                  </TableCell>
                  <TableCell>{item.expiry_date?.slice(0, 10) || '-'}</TableCell>
                  <TableCell className="font-mono">{item.bin_location || '-'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        );

      case 'dead-slow-stock':
        return (
          <Table>
            <TableHeader>
              <TableRow className="bg-gray-50">
                <TableHead className="font-semibold">Material Code</TableHead>
                <TableHead className="font-semibold">Name</TableHead>
                <TableHead className="font-semibold">Category</TableHead>
                <TableHead className="font-semibold text-right">Stock</TableHead>
                <TableHead className="font-semibold">Last Movement</TableHead>
                <TableHead className="font-semibold text-right">Days Idle</TableHead>
                <TableHead className="font-semibold">Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((item, idx) => (
                <TableRow key={idx} className="hover:bg-gray-50">
                  <TableCell className="font-mono font-medium">{item.material_code}</TableCell>
                  <TableCell>{item.material_name}</TableCell>
                  <TableCell>{item.category}</TableCell>
                  <TableCell className="text-right tabular-nums font-medium">{item.current_stock}</TableCell>
                  <TableCell>{item.last_movement_date?.slice(0, 10) || '-'}</TableCell>
                  <TableCell className="text-right tabular-nums">{item.days_since_movement}</TableCell>
                  <TableCell><Badge className={getStatusBadge(item.status)}>{item.status}</Badge></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        );

      case 'daily-summary':
        return (
          <Table>
            <TableHeader>
              <TableRow className="bg-gray-50">
                <TableHead className="font-semibold">Date</TableHead>
                <TableHead className="font-semibold text-right">Inward Count</TableHead>
                <TableHead className="font-semibold text-right">Inward Qty</TableHead>
                <TableHead className="font-semibold text-right">Outward Count</TableHead>
                <TableHead className="font-semibold text-right">Outward Qty</TableHead>
                <TableHead className="font-semibold text-right">Transfer Count</TableHead>
                <TableHead className="font-semibold text-right">Transfer Qty</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((item, idx) => (
                <TableRow key={idx} className="hover:bg-gray-50">
                  <TableCell className="font-medium">{item.date}</TableCell>
                  <TableCell className="text-right tabular-nums">{item.inward_count}</TableCell>
                  <TableCell className="text-right tabular-nums text-green-600 font-medium">{item.inward_qty}</TableCell>
                  <TableCell className="text-right tabular-nums">{item.outward_count}</TableCell>
                  <TableCell className="text-right tabular-nums text-red-600 font-medium">{item.outward_qty}</TableCell>
                  <TableCell className="text-right tabular-nums">{item.transfer_count}</TableCell>
                  <TableCell className="text-right tabular-nums text-blue-600">{item.transfer_qty}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        );

      case 'stock-reconciliation':
        return (
          <Table>
            <TableHeader>
              <TableRow className="bg-gray-50">
                <TableHead className="font-semibold">Material Code</TableHead>
                <TableHead className="font-semibold">Name</TableHead>
                <TableHead className="font-semibold text-right">System Stock</TableHead>
                <TableHead className="font-semibold text-right">Bin Stock</TableHead>
                <TableHead className="font-semibold text-right">Variance</TableHead>
                <TableHead className="font-semibold text-right">Var %</TableHead>
                <TableHead className="font-semibold">Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((item, idx) => (
                <TableRow key={idx} className="hover:bg-gray-50">
                  <TableCell className="font-mono font-medium">{item.material_code}</TableCell>
                  <TableCell>{item.material_name}</TableCell>
                  <TableCell className="text-right tabular-nums">{item.system_stock}</TableCell>
                  <TableCell className="text-right tabular-nums">{item.bin_stock}</TableCell>
                  <TableCell className={`text-right tabular-nums font-medium ${item.variance > 0 ? 'text-blue-600' : item.variance < 0 ? 'text-red-600' : ''}`}>
                    {item.variance > 0 ? '+' : ''}{item.variance}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">{item.variance_percent}%</TableCell>
                  <TableCell><Badge className={getStatusBadge(item.status)}>{item.status}</Badge></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        );

      case 'user-activity':
        return (
          <Table>
            <TableHeader>
              <TableRow className="bg-gray-50">
                <TableHead className="font-semibold">Timestamp</TableHead>
                <TableHead className="font-semibold">User</TableHead>
                <TableHead className="font-semibold">Role</TableHead>
                <TableHead className="font-semibold">Action</TableHead>
                <TableHead className="font-semibold">Entity</TableHead>
                <TableHead className="font-semibold">Details</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((item, idx) => (
                <TableRow key={idx} className="hover:bg-gray-50">
                  <TableCell className="text-sm">{item.timestamp?.slice(0, 19).replace('T', ' ')}</TableCell>
                  <TableCell className="font-medium">{item.performed_by_name}</TableCell>
                  <TableCell><Badge variant="outline">{item.performed_by_role}</Badge></TableCell>
                  <TableCell><Badge className={getStatusBadge(item.action)}>{item.action}</Badge></TableCell>
                  <TableCell className="capitalize">{item.entity_type}</TableCell>
                  <TableCell className="text-sm text-gray-600 max-w-xs truncate">{item.entity_name || '-'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        );

      case 'putaway-pending':
        return (
          <Table>
            <TableHeader>
              <TableRow className="bg-gray-50">
                <TableHead className="font-semibold">GRN #</TableHead>
                <TableHead className="font-semibold">Vendor</TableHead>
                <TableHead className="font-semibold">Material</TableHead>
                <TableHead className="font-semibold text-right">Quantity</TableHead>
                <TableHead className="font-semibold">Target Bin</TableHead>
                <TableHead className="font-semibold">Status</TableHead>
                <TableHead className="font-semibold">Created</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((item, idx) => (
                <TableRow key={idx} className="hover:bg-gray-50">
                  <TableCell className="font-mono">{item.grn_number || '-'}</TableCell>
                  <TableCell>{item.vendor_name || '-'}</TableCell>
                  <TableCell className="font-mono font-medium">{item.material_code}</TableCell>
                  <TableCell className="text-right tabular-nums font-medium">{item.quantity}</TableCell>
                  <TableCell className="font-mono">{item.bin_code || '-'}</TableCell>
                  <TableCell><Badge className={getStatusBadge(item.status)}>{item.status}</Badge></TableCell>
                  <TableCell className="text-sm">{item.created_at?.slice(0, 10)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        );

      case 'fifo-compliance':
      case 'stock-summary':
      default:
        return (
          <Table>
            <TableHeader>
              <TableRow className="bg-gray-50">
                <TableHead className="font-semibold">Material Code</TableHead>
                <TableHead className="font-semibold">Name</TableHead>
                <TableHead className="font-semibold">Category</TableHead>
                <TableHead className="font-semibold">UOM</TableHead>
                <TableHead className="font-semibold text-right">Stock</TableHead>
                <TableHead className="font-semibold">Method</TableHead>
                <TableHead className="font-semibold">Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((item, idx) => (
                <TableRow key={idx} className="hover:bg-gray-50">
                  <TableCell className="font-mono font-medium">{item.material_code}</TableCell>
                  <TableCell>{item.name || item.material_name}</TableCell>
                  <TableCell>{item.category}</TableCell>
                  <TableCell>{item.uom}</TableCell>
                  <TableCell className="text-right tabular-nums font-medium">{item.current_stock || 0}</TableCell>
                  <TableCell><Badge variant="outline">{item.stock_method}</Badge></TableCell>
                  <TableCell>
                    {item.compliance_status ? (
                      <Badge className={getStatusBadge(item.compliance_status)}>{item.compliance_status}</Badge>
                    ) : (
                      <Badge className={
                        (item.current_stock || 0) <= 0 ? 'bg-red-100 text-red-700' :
                        (item.current_stock || 0) <= (item.reorder_point || 50) ? 'bg-amber-100 text-amber-700' :
                        'bg-green-100 text-green-700'
                      }>
                        {(item.current_stock || 0) <= 0 ? 'Out of Stock' : 
                         (item.current_stock || 0) <= (item.reorder_point || 50) ? 'Low Stock' : 'In Stock'}
                      </Badge>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        );
    }
  };

  const currentCategory = REPORT_CATEGORIES.find(c => c.id === selectedCategory);
  const currentReport = currentCategory?.reports.find(r => r.id === selectedReport);

  // Download specific report
  const downloadReport = async (reportId, format) => {
    const params = Object.fromEntries(
      Object.entries(filters).filter(([_, v]) => v !== '')
    );
    
    try {
      setExporting(true);
      const token = localStorage.getItem('auth_token');
      const queryParams = new URLSearchParams({ 
        report_type: reportId, 
        ...params,
        ...(token && { token })
      });
      
      const url = `${process.env.REACT_APP_BACKEND_URL}/api/reports/export/${format === 'excel' ? 'excel' : 'pdf'}?${queryParams.toString()}`;
      
      // Use fetch with credentials to include cookies
      const response = await fetch(url, {
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error('Download failed');
      }
      
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `${reportId}-${new Date().toISOString().slice(0,10)}.${format === 'excel' ? 'xlsx' : 'pdf'}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
      
      const reportName = allReports.find(r => r.id === reportId)?.name || reportId;
      toast.success(`Downloaded ${reportName} as ${format.toUpperCase()}`);
    } catch (error) {
      console.error('Download error:', error);
      toast.error('Failed to download report');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
          <p className="text-gray-500">Generate and export inventory reports</p>
        </div>
        <div className="flex gap-2">
          {/* Current Report Export */}
          <Button 
            variant="outline" 
            onClick={() => handleExport('excel')}
            className="flex items-center gap-2"
            data-testid="export-excel-btn"
          >
            <FileSpreadsheet className="w-4 h-4" />
            Export Current
          </Button>
          
          {/* Download Dialog for selecting reports */}
          <Dialog open={isDownloadDialogOpen} onOpenChange={setIsDownloadDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-[#f59e0b] hover:bg-[#d97706] flex items-center gap-2" data-testid="download-reports-btn">
                <Download className="w-4 h-4" />
                Download Reports
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <Download className="w-5 h-5" />
                  Download Reports
                </DialogTitle>
                <DialogDescription>
                  Select a report and format to download. Applied filters will be included.
                </DialogDescription>
              </DialogHeader>
              
              <div className="space-y-4 mt-4">
                {REPORT_CATEGORIES.map((category) => {
                  // Hide audit reports if user doesn't have permission
                  if (category.id === 'audit' && !canViewAuditReports) return null;
                  
                  const Icon = category.icon;
                  
                  return (
                    <div key={category.id} className="border rounded-lg p-4">
                      <h3 className="font-semibold flex items-center gap-2 mb-3 text-gray-700">
                        <Icon className="w-4 h-4" />
                        {category.name}
                      </h3>
                      <div className="grid gap-2">
                        {category.reports.map((report) => (
                          <div 
                            key={report.id} 
                            className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                          >
                            <div>
                              <p className="font-medium text-sm">{report.name}</p>
                              <p className="text-xs text-gray-500">{report.description}</p>
                            </div>
                            <div className="flex gap-2">
                              <Button 
                                size="sm" 
                                variant="outline"
                                disabled={exporting}
                                onClick={async () => {
                                  await downloadReport(report.id, 'excel');
                                  setIsDownloadDialogOpen(false);
                                }}
                                className="flex items-center gap-1"
                                data-testid={`download-excel-${report.id}`}
                              >
                                <FileSpreadsheet className="w-3 h-3" />
                                Excel
                              </Button>
                              <Button 
                                size="sm" 
                                variant="outline"
                                disabled={exporting}
                                onClick={async () => {
                                  await downloadReport(report.id, 'pdf');
                                  setIsDownloadDialogOpen(false);
                                }}
                                className="flex items-center gap-1"
                                data-testid={`download-pdf-${report.id}`}
                              >
                                <FileText className="w-3 h-3" />
                                PDF
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
              
              {/* Filter Info */}
              {(filters.start_date || filters.end_date || filters.material_code) && (
                <div className="mt-4 p-3 bg-amber-50 rounded-lg border border-amber-200">
                  <p className="text-sm text-amber-800 flex items-center gap-2">
                    <Filter className="w-4 h-4" />
                    <span className="font-medium">Active Filters:</span>
                    {filters.start_date && <Badge variant="outline" className="text-xs">From: {filters.start_date}</Badge>}
                    {filters.end_date && <Badge variant="outline" className="text-xs">To: {filters.end_date}</Badge>}
                    {filters.material_code && <Badge variant="outline" className="text-xs">Material: {filters.material_code}</Badge>}
                  </p>
                </div>
              )}
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Report Selection Sidebar */}
        <div className="lg:col-span-1 space-y-4">
          {REPORT_CATEGORIES.map((category) => {
            // Hide audit reports if user doesn't have permission
            if (category.id === 'audit' && !canViewAuditReports) return null;
            
            const Icon = category.icon;
            const isSelected = selectedCategory === category.id;
            
            return (
              <Card 
                key={category.id} 
                className={`cursor-pointer transition-all ${isSelected ? 'ring-2 ring-[#f59e0b] border-[#f59e0b]' : 'hover:border-gray-300'}`}
                onClick={() => {
                  setSelectedCategory(category.id);
                  setSelectedReport(category.reports[0].id);
                }}
              >
                <CardHeader className="p-4">
                  <CardTitle className="flex items-center gap-2 text-sm">
                    <Icon className={`w-4 h-4 ${isSelected ? 'text-[#f59e0b]' : 'text-gray-500'}`} />
                    {category.name}
                  </CardTitle>
                </CardHeader>
                {isSelected && (
                  <CardContent className="p-0 pb-2">
                    <div className="space-y-1 px-2">
                      {category.reports.map((report) => (
                        <button
                          key={report.id}
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedReport(report.id);
                          }}
                          className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${
                            selectedReport === report.id
                              ? 'bg-[#f59e0b] text-white'
                              : 'hover:bg-gray-100 text-gray-700'
                          }`}
                          data-testid={`report-${report.id}`}
                        >
                          <div className="flex items-center justify-between">
                            <span>{report.name}</span>
                            <ChevronRight className="w-4 h-4 opacity-50" />
                          </div>
                        </button>
                      ))}
                    </div>
                  </CardContent>
                )}
              </Card>
            );
          })}
        </div>

        {/* Report Content */}
        <div className="lg:col-span-3 space-y-4">
          {/* Filters */}
          <Card className="border border-gray-200">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Filter className="w-4 h-4" />
                Filters
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
                <div className="space-y-2">
                  <Label className="text-xs text-gray-500">Start Date</Label>
                  <Input
                    type="date"
                    value={filters.start_date}
                    onChange={(e) => handleFilterChange('start_date', e.target.value)}
                    data-testid="filter-start-date"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs text-gray-500">End Date</Label>
                  <Input
                    type="date"
                    value={filters.end_date}
                    onChange={(e) => handleFilterChange('end_date', e.target.value)}
                    data-testid="filter-end-date"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs text-gray-500">Material Code</Label>
                  <Input
                    placeholder="Search material..."
                    value={filters.material_code}
                    onChange={(e) => handleFilterChange('material_code', e.target.value)}
                    data-testid="filter-material"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs text-gray-500">Batch Number</Label>
                  <Input
                    placeholder="Search batch..."
                    value={filters.batch_number}
                    onChange={(e) => handleFilterChange('batch_number', e.target.value)}
                    data-testid="filter-batch"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs text-gray-500">Bin Code</Label>
                  <Input
                    placeholder="Search bin..."
                    value={filters.bin_code}
                    onChange={(e) => handleFilterChange('bin_code', e.target.value)}
                    data-testid="filter-bin"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs text-gray-500">Zone</Label>
                  <Select value={filters.zone || "all"} onValueChange={(v) => handleFilterChange('zone', v === "all" ? "" : v)}>
                    <SelectTrigger data-testid="filter-zone">
                      <SelectValue placeholder="All zones" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Zones</SelectItem>
                      <SelectItem value="A">Zone A</SelectItem>
                      <SelectItem value="B">Zone B</SelectItem>
                      <SelectItem value="C">Zone C</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-end gap-2 col-span-full md:col-span-1 lg:col-span-2">
                  <Button onClick={applyFilters} className="bg-[#f59e0b] hover:bg-[#d97706]" data-testid="apply-filters-btn">
                    <Search className="w-4 h-4 mr-2" />
                    Apply Filters
                  </Button>
                  <Button variant="outline" onClick={clearFilters} data-testid="clear-filters-btn">
                    Clear
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Report Table */}
          <Card className="border border-gray-200">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Layers className="w-5 h-5 text-[#f59e0b]" />
                    {currentReport?.name || 'Report'}
                  </CardTitle>
                  <CardDescription>{currentReport?.description}</CardDescription>
                </div>
                <div className="flex items-center gap-4">
                  <Badge variant="outline" className="text-sm">
                    {total} records
                  </Badge>
                  <Button variant="ghost" size="sm" onClick={loadReport}>
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                {renderTable()}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Reports;
