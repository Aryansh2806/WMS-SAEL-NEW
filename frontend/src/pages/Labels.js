import React, { useState, useEffect, useRef } from 'react';
import { labelAPI, materialAPI, grnAPI } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Checkbox } from '../components/ui/checkbox';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Textarea } from '../components/ui/textarea';
import { Plus, Printer, Tags, Package, History, RefreshCw, CheckSquare, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import QRCode from 'react-qr-code';
import Barcode from 'react-barcode';

const Labels = () => {
  const { hasPermission } = useAuth();
  const [labels, setLabels] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [grns, setGrns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('labels');
  const [printLogs, setPrintLogs] = useState([]);
  
  // Dialog states
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [selectedLabel, setSelectedLabel] = useState(null);
  const [isReprintDialogOpen, setIsReprintDialogOpen] = useState(false);
  const [reprintReason, setReprintReason] = useState('');
  const [isHistoryDialogOpen, setIsHistoryDialogOpen] = useState(false);
  const [labelHistory, setLabelHistory] = useState([]);
  
  // Bulk selection
  const [selectedLabels, setSelectedLabels] = useState([]);
  const [isBulkMode, setIsBulkMode] = useState(false);
  
  // Create form
  const [formData, setFormData] = useState({
    material_id: '',
    grn_id: '',
    batch_number: '',
    quantity: 1,
    uom: '',
    bin_location: '',
    manufacturing_date: '',
    expiry_date: '',
    storage_condition: ''
  });
  
  const printRef = useRef();

  const canCreate = hasPermission(['Admin', 'Store In-Charge', 'Warehouse Operator']);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (activeTab === 'logs') {
      loadPrintLogs();
    }
  }, [activeTab]);

  const loadData = async () => {
    try {
      const [labelsRes, materialsRes, grnsRes] = await Promise.all([
        labelAPI.getAll(),
        materialAPI.getAll(),
        grnAPI.getAll()
      ]);
      setLabels(labelsRes.data);
      setMaterials(materialsRes.data);
      setGrns(grnsRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadPrintLogs = async () => {
    try {
      const response = await labelAPI.getAllPrintLogs();
      setPrintLogs(response.data);
    } catch (error) {
      console.error('Failed to load print logs:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.material_id || formData.quantity < 1) {
      toast.error('Select material and enter quantity');
      return;
    }
    
    try {
      const response = await labelAPI.create(formData);
      toast.success('Label created successfully');
      setIsCreateDialogOpen(false);
      setSelectedLabel(response.data);
      resetForm();
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create label');
    }
  };

  const handlePrint = async (label) => {
    try {
      // Log the print action
      await labelAPI.logPrint(label.label_id, 1);
      
      // Open print window
      printLabelContent(label);
      
      toast.success('Print logged successfully');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to log print');
    }
  };

  const handleReprint = async () => {
    if (!reprintReason || reprintReason.trim().length < 3) {
      toast.error('Please provide a reason for reprinting (minimum 3 characters)');
      return;
    }
    
    try {
      await labelAPI.logReprint(selectedLabel.label_id, {
        label_id: selectedLabel.label_id,
        reason: reprintReason.trim(),
        copies: 1
      });
      
      // Open print window
      printLabelContent(selectedLabel);
      
      toast.success('Reprint logged successfully');
      setIsReprintDialogOpen(false);
      setReprintReason('');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to log reprint');
    }
  };

  const handleBulkPrint = async () => {
    if (selectedLabels.length === 0) {
      toast.error('Select at least one label to print');
      return;
    }
    
    try {
      await labelAPI.bulkPrint({
        label_ids: selectedLabels,
        copies: 1
      });
      
      // Print all selected labels
      const labelsToPrint = labels.filter(l => selectedLabels.includes(l.label_id));
      printBulkLabels(labelsToPrint);
      
      toast.success(`Bulk print logged for ${selectedLabels.length} labels`);
      setSelectedLabels([]);
      setIsBulkMode(false);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to log bulk print');
    }
  };

  const handleViewHistory = async (label) => {
    try {
      const response = await labelAPI.getPrintHistory(label.label_id);
      setLabelHistory(response.data);
      setSelectedLabel(label);
      setIsHistoryDialogOpen(true);
    } catch (error) {
      toast.error('Failed to load print history');
    }
  };

  const toggleLabelSelection = (labelId) => {
    setSelectedLabels(prev => 
      prev.includes(labelId) 
        ? prev.filter(id => id !== labelId)
        : [...prev, labelId]
    );
  };

  const selectAllLabels = () => {
    if (selectedLabels.length === labels.length) {
      setSelectedLabels([]);
    } else {
      setSelectedLabels(labels.map(l => l.label_id));
    }
  };

  const printLabelContent = (label) => {
    const printWindow = window.open('', '_blank');
    printWindow.document.write(generateLabelHTML(label));
    printWindow.document.close();
    printWindow.print();
  };

  const printBulkLabels = (labelsToPrint) => {
    const printWindow = window.open('', '_blank');
    const labelsHTML = labelsToPrint.map(l => generateLabelHTML(l, false)).join('<div style="page-break-after: always;"></div>');
    printWindow.document.write(`
      <html>
        <head>
          <title>Bulk Print Labels</title>
          <style>
            body { font-family: 'IBM Plex Sans', Arial, sans-serif; padding: 0; margin: 0; }
            @media print { body { margin: 0; } .page-break { page-break-after: always; } }
          </style>
        </head>
        <body>${labelsHTML}</body>
      </html>
    `);
    printWindow.document.close();
    printWindow.print();
  };

  const generateLabelHTML = (label, standalone = true) => {
    const wrapper = standalone ? `<html><head><title>Print Label</title><style>
      body { font-family: 'IBM Plex Sans', Arial, sans-serif; padding: 20px; margin: 0; }
      @media print { body { margin: 0; padding: 10px; } }
    </style></head><body>` : '';
    const wrapperEnd = standalone ? '</body></html>' : '';
    
    return `${wrapper}
      <div style="border: 2px solid #000; padding: 15px; max-width: 400px; margin: auto;">
        <div style="text-align: center; font-size: 16px; font-weight: bold; border-bottom: 1px solid #000; padding-bottom: 10px; margin-bottom: 10px;">
          WMS Pro - Material Label
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px;">
          <div><span style="color: #666;">Material Code:</span><br/><strong style="font-family: monospace; font-size: 14px;">${label.material_code}</strong></div>
          <div><span style="color: #666;">Quantity:</span><br/><strong style="font-size: 14px;">${label.quantity} ${label.uom || 'PCS'}</strong></div>
          <div style="grid-column: span 2;"><span style="color: #666;">Description:</span><br/><strong>${label.material_name}</strong></div>
          <div><span style="color: #666;">Batch/Lot:</span><br/><strong style="font-family: monospace;">${label.batch_number}</strong></div>
          <div><span style="color: #666;">GRN:</span><br/><strong style="font-family: monospace;">${label.grn_number || 'N/A'}</strong></div>
          <div><span style="color: #666;">Receipt Date:</span><br/><strong>${label.date_of_receipt ? new Date(label.date_of_receipt).toLocaleDateString() : 'N/A'}</strong></div>
          <div><span style="color: #666;">Bin Location:</span><br/><strong style="font-family: monospace;">${label.bin_location || 'N/A'}</strong></div>
          ${label.expiry_date ? `<div><span style="color: #666;">Expiry Date:</span><br/><strong style="color: ${new Date(label.expiry_date) < new Date() ? 'red' : 'inherit'};">${label.expiry_date}</strong></div>` : ''}
          ${label.storage_condition ? `<div><span style="color: #666;">Storage:</span><br/><strong style="text-transform: capitalize;">${label.storage_condition.replace(/_/g, ' ')}</strong></div>` : ''}
        </div>
        <div style="display: flex; justify-content: center; gap: 20px; margin-top: 15px; padding-top: 15px; border-top: 1px solid #000;">
          <div style="text-align: center;">
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=80x80&data=${encodeURIComponent(label.qr_data)}" alt="QR Code" style="width: 80px; height: 80px;" />
            <div style="font-size: 10px; color: #666; margin-top: 4px;">QR Code</div>
          </div>
          <div style="text-align: center;">
            <svg id="barcode-${label.label_id}"></svg>
            <div style="font-size: 10px; color: #666; margin-top: 4px;">Barcode</div>
          </div>
        </div>
      </div>
    ${wrapperEnd}`;
  };

  const resetForm = () => {
    setFormData({
      material_id: '',
      grn_id: '',
      batch_number: '',
      quantity: 1,
      uom: '',
      bin_location: '',
      manufacturing_date: '',
      expiry_date: '',
      storage_condition: ''
    });
  };

  return (
    <div className="space-y-6">
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="flex flex-col sm:flex-row justify-between gap-4">
          <TabsList>
            <TabsTrigger value="labels" className="flex items-center gap-2" data-testid="tab-labels">
              <Tags className="w-4 h-4" />
              Labels
            </TabsTrigger>
            <TabsTrigger value="logs" className="flex items-center gap-2" data-testid="tab-print-logs">
              <History className="w-4 h-4" />
              Print Logs
            </TabsTrigger>
          </TabsList>

          <div className="flex gap-2">
            {isBulkMode && selectedLabels.length > 0 && (
              <Button onClick={handleBulkPrint} className="bg-green-600 hover:bg-green-700" data-testid="bulk-print-btn">
                <Printer className="w-4 h-4 mr-2" />
                Print Selected ({selectedLabels.length})
              </Button>
            )}
            <Button
              variant={isBulkMode ? "secondary" : "outline"}
              onClick={() => { setIsBulkMode(!isBulkMode); setSelectedLabels([]); }}
              data-testid="toggle-bulk-mode-btn"
            >
              <CheckSquare className="w-4 h-4 mr-2" />
              {isBulkMode ? 'Exit Bulk Mode' : 'Bulk Select'}
            </Button>
            {canCreate && (
              <Dialog open={isCreateDialogOpen} onOpenChange={(open) => { setIsCreateDialogOpen(open); if (!open) resetForm(); }}>
                <DialogTrigger asChild>
                  <Button className="bg-[#f59e0b] hover:bg-[#d97706]" data-testid="create-label-btn">
                    <Plus className="w-4 h-4 mr-2" />
                    Create Label
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-lg">
                  <DialogHeader>
                    <DialogTitle>Create Label Manually</DialogTitle>
                    <DialogDescription>Labels are auto-generated when GRN is saved. Use this for manual label creation.</DialogDescription>
                  </DialogHeader>
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-2">
                      <Label>Material *</Label>
                      <Select value={formData.material_id} onValueChange={(v) => {
                        const mat = materials.find(m => m.material_id === v);
                        setFormData({ ...formData, material_id: v, uom: mat?.uom || '' });
                      }}>
                        <SelectTrigger data-testid="label-material-select">
                          <SelectValue placeholder="Select Material" />
                        </SelectTrigger>
                        <SelectContent>
                          {materials.map((mat) => (
                            <SelectItem key={mat.material_id} value={mat.material_id}>
                              {mat.material_code} - {mat.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label>GRN Reference (Optional)</Label>
                      <Select value={formData.grn_id || 'none'} onValueChange={(v) => setFormData({ ...formData, grn_id: v === 'none' ? '' : v })}>
                        <SelectTrigger data-testid="label-grn-select">
                          <SelectValue placeholder="Select GRN" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">None</SelectItem>
                          {grns.map((grn) => (
                            <SelectItem key={grn.grn_id} value={grn.grn_id}>
                              {grn.grn_number} - {grn.vendor_name || grn.supplier_name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Batch Number</Label>
                        <Input
                          value={formData.batch_number}
                          onChange={(e) => setFormData({ ...formData, batch_number: e.target.value })}
                          placeholder="Auto-generated if empty"
                          data-testid="label-batch-input"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Quantity *</Label>
                        <Input
                          type="number"
                          value={formData.quantity}
                          onChange={(e) => setFormData({ ...formData, quantity: parseInt(e.target.value) || 0 })}
                          min={1}
                          required
                          data-testid="label-quantity-input"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Expiry Date</Label>
                        <Input
                          type="date"
                          value={formData.expiry_date}
                          onChange={(e) => setFormData({ ...formData, expiry_date: e.target.value })}
                          data-testid="label-expiry-input"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Bin Location</Label>
                        <Input
                          value={formData.bin_location}
                          onChange={(e) => setFormData({ ...formData, bin_location: e.target.value })}
                          placeholder="e.g., A-01-02-03"
                          data-testid="label-bin-input"
                        />
                      </div>
                    </div>

                    <div className="flex justify-end gap-3 pt-4">
                      <Button type="button" variant="outline" onClick={() => { setIsCreateDialogOpen(false); resetForm(); }}>
                        Cancel
                      </Button>
                      <Button type="submit" className="bg-[#f59e0b] hover:bg-[#d97706]" data-testid="label-submit-btn">
                        Create Label
                      </Button>
                    </div>
                  </form>
                </DialogContent>
              </Dialog>
            )}
          </div>
        </div>

        {/* Labels Tab */}
        <TabsContent value="labels">
          {/* Label Preview Dialog */}
          <Dialog open={!!selectedLabel && !isReprintDialogOpen && !isHistoryDialogOpen} onOpenChange={() => setSelectedLabel(null)}>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>Label Preview</DialogTitle>
              </DialogHeader>
              {selectedLabel && (
                <div className="space-y-4">
                  <div ref={printRef} className="border-2 border-gray-900 rounded-lg p-4 bg-white print-label">
                    <div className="text-center font-bold text-lg border-b border-gray-900 pb-3 mb-4">
                      WMS Pro - Material Label
                    </div>
                    
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <span className="text-gray-500 text-xs">Material Code</span>
                        <p className="font-mono font-bold">{selectedLabel.material_code}</p>
                      </div>
                      <div>
                        <span className="text-gray-500 text-xs">Quantity</span>
                        <p className="font-bold">{selectedLabel.quantity} {selectedLabel.uom || 'PCS'}</p>
                      </div>
                      <div className="col-span-2">
                        <span className="text-gray-500 text-xs">Description</span>
                        <p className="font-medium">{selectedLabel.material_name}</p>
                      </div>
                      <div>
                        <span className="text-gray-500 text-xs">Batch/Lot</span>
                        <p className="font-mono font-medium">{selectedLabel.batch_number}</p>
                      </div>
                      <div>
                        <span className="text-gray-500 text-xs">GRN Number</span>
                        <p className="font-mono font-medium">{selectedLabel.grn_number || 'N/A'}</p>
                      </div>
                      <div>
                        <span className="text-gray-500 text-xs">Receipt Date</span>
                        <p className="font-medium">{selectedLabel.date_of_receipt ? new Date(selectedLabel.date_of_receipt).toLocaleDateString() : 'N/A'}</p>
                      </div>
                      <div>
                        <span className="text-gray-500 text-xs">Bin Location</span>
                        <p className="font-mono font-medium">{selectedLabel.bin_location || 'N/A'}</p>
                      </div>
                      {selectedLabel.expiry_date && (
                        <div>
                          <span className="text-gray-500 text-xs">Expiry Date</span>
                          <p className={`font-medium ${new Date(selectedLabel.expiry_date) < new Date() ? 'text-red-600' : ''}`}>
                            {selectedLabel.expiry_date}
                          </p>
                        </div>
                      )}
                      {selectedLabel.storage_condition && (
                        <div>
                          <span className="text-gray-500 text-xs">Storage</span>
                          <p className="font-medium capitalize">{selectedLabel.storage_condition.replace(/_/g, ' ')}</p>
                        </div>
                      )}
                    </div>

                    <div className="flex gap-4 justify-center mt-4 pt-4 border-t border-gray-900">
                      <div className="text-center">
                        <QRCode value={selectedLabel.qr_data} size={80} />
                        <p className="text-xs text-gray-500 mt-1">QR Code</p>
                      </div>
                      <div className="text-center overflow-hidden">
                        <Barcode value={selectedLabel.barcode_data} width={1} height={40} fontSize={10} margin={0} />
                        <p className="text-xs text-gray-500 mt-1">Barcode</p>
                      </div>
                    </div>
                  </div>

                  {/* Print info */}
                  {selectedLabel.print_count > 0 && (
                    <div className="flex items-center justify-between text-sm text-gray-500 bg-gray-50 p-2 rounded">
                      <span>Printed {selectedLabel.print_count} time(s)</span>
                      <span>Last: {selectedLabel.last_printed_by}</span>
                    </div>
                  )}

                  <div className="flex gap-2">
                    {selectedLabel.print_count === 0 ? (
                      <Button onClick={() => handlePrint(selectedLabel)} className="flex-1 bg-[#f59e0b] hover:bg-[#d97706]" data-testid="print-label-btn">
                        <Printer className="w-4 h-4 mr-2" />
                        Print Label
                      </Button>
                    ) : (
                      <Button onClick={() => setIsReprintDialogOpen(true)} className="flex-1 bg-blue-600 hover:bg-blue-700" data-testid="reprint-label-btn">
                        <RefreshCw className="w-4 h-4 mr-2" />
                        Reprint Label
                      </Button>
                    )}
                    <Button variant="outline" onClick={() => handleViewHistory(selectedLabel)} data-testid="view-history-btn">
                      <History className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              )}
            </DialogContent>
          </Dialog>

          {/* Reprint Reason Dialog */}
          <Dialog open={isReprintDialogOpen} onOpenChange={setIsReprintDialogOpen}>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-amber-500" />
                  Reprint Reason Required
                </DialogTitle>
                <DialogDescription>
                  Please provide a reason for reprinting this label. This will be logged for audit purposes.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Reason for Reprint *</Label>
                  <Textarea
                    value={reprintReason}
                    onChange={(e) => setReprintReason(e.target.value)}
                    placeholder="e.g., Label damaged, Wrong information, Lost label..."
                    className="min-h-[100px]"
                    data-testid="reprint-reason-input"
                  />
                </div>
                <div className="flex justify-end gap-3">
                  <Button variant="outline" onClick={() => { setIsReprintDialogOpen(false); setReprintReason(''); }}>
                    Cancel
                  </Button>
                  <Button onClick={handleReprint} className="bg-blue-600 hover:bg-blue-700" data-testid="confirm-reprint-btn">
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Confirm Reprint
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>

          {/* Print History Dialog */}
          <Dialog open={isHistoryDialogOpen} onOpenChange={setIsHistoryDialogOpen}>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Print History - {selectedLabel?.material_code}</DialogTitle>
              </DialogHeader>
              {labelHistory.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <History className="w-12 h-12 mx-auto mb-2 opacity-20" />
                  <p>No print history found</p>
                </div>
              ) : (
                <div className="max-h-96 overflow-y-auto">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-gray-50">
                        <TableHead>Action</TableHead>
                        <TableHead>Date/Time</TableHead>
                        <TableHead>Printed By</TableHead>
                        <TableHead>Copies</TableHead>
                        <TableHead>Reason</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {labelHistory.map((log, index) => (
                        <TableRow key={index}>
                          <TableCell>
                            <Badge className={log.action === 'reprint' ? 'badge-hold' : 'badge-available'}>
                              {log.action}
                            </Badge>
                          </TableCell>
                          <TableCell>{new Date(log.printed_at).toLocaleString()}</TableCell>
                          <TableCell>{log.printed_by_name}</TableCell>
                          <TableCell>{log.quantity_printed}</TableCell>
                          <TableCell className="max-w-xs truncate">{log.reason || '-'}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </DialogContent>
          </Dialog>

          {/* Labels Grid */}
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3].map((i) => (
                <Card key={i} className="animate-pulse">
                  <CardContent className="pt-6">
                    <div className="h-48 bg-gray-200 rounded"></div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : labels.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Tags className="w-16 h-16 mx-auto mb-4 opacity-20" />
              <p className="text-lg">No labels generated yet</p>
              <p className="text-sm">Labels are auto-created when GRN is saved</p>
            </div>
          ) : (
            <>
              {isBulkMode && (
                <div className="flex items-center gap-4 p-3 bg-blue-50 rounded-lg border border-blue-200 mb-4">
                  <Checkbox
                    checked={selectedLabels.length === labels.length}
                    onCheckedChange={selectAllLabels}
                    data-testid="select-all-labels"
                  />
                  <span className="text-sm text-blue-700">
                    {selectedLabels.length === 0 
                      ? 'Select labels for bulk printing' 
                      : `${selectedLabels.length} of ${labels.length} selected`}
                  </span>
                </div>
              )}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {labels.map((label) => (
                  <Card
                    key={label.label_id}
                    className={`border cursor-pointer card-hover ${
                      selectedLabels.includes(label.label_id) ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                    }`}
                    onClick={() => isBulkMode ? toggleLabelSelection(label.label_id) : setSelectedLabel(label)}
                    data-testid={`label-card-${label.label_id}`}
                  >
                    <CardHeader className="pb-2">
                      <div className="flex justify-between items-start">
                        <div className="flex items-center gap-2">
                          {isBulkMode && (
                            <Checkbox
                              checked={selectedLabels.includes(label.label_id)}
                              onCheckedChange={() => toggleLabelSelection(label.label_id)}
                              onClick={(e) => e.stopPropagation()}
                            />
                          )}
                          <CardTitle className="text-base font-mono">{label.material_code}</CardTitle>
                        </div>
                        <div className="flex items-center gap-2">
                          {label.print_count > 0 && (
                            <Badge variant="outline" className="text-xs">
                              <Printer className="w-3 h-3 mr-1" />
                              {label.print_count}
                            </Badge>
                          )}
                          <Package className="w-5 h-5 text-gray-400" />
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <p className="text-sm text-gray-600 truncate">{label.material_name}</p>
                      
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span className="text-gray-500 text-xs">Batch</span>
                          <p className="font-mono font-medium truncate">{label.batch_number}</p>
                        </div>
                        <div>
                          <span className="text-gray-500 text-xs">Qty</span>
                          <p className="font-bold tabular-nums">{label.quantity} {label.uom || 'PCS'}</p>
                        </div>
                        {label.grn_number && (
                          <div>
                            <span className="text-gray-500 text-xs">GRN</span>
                            <p className="font-mono text-xs truncate">{label.grn_number}</p>
                          </div>
                        )}
                        {label.bin_location && (
                          <div>
                            <span className="text-gray-500 text-xs">Bin</span>
                            <p className="font-mono text-xs">{label.bin_location}</p>
                          </div>
                        )}
                      </div>

                      <div className="flex gap-2 justify-center pt-2 border-t border-gray-100">
                        <QRCode value={label.qr_data} size={50} />
                        <div className="overflow-hidden">
                          <Barcode value={label.barcode_data} width={1} height={30} fontSize={8} margin={0} />
                        </div>
                      </div>

                      <p className="text-xs text-gray-400 text-center">
                        Created: {new Date(label.created_at).toLocaleDateString()}
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </>
          )}
        </TabsContent>

        {/* Print Logs Tab */}
        <TabsContent value="logs">
          <Card className="border border-gray-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="w-5 h-5" />
                Print Log History
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {printLogs.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <History className="w-12 h-12 mx-auto mb-2 opacity-20" />
                  <p>No print logs found</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-gray-50">
                        <TableHead>Action</TableHead>
                        <TableHead>Label ID</TableHead>
                        <TableHead>Date/Time</TableHead>
                        <TableHead>Printed By</TableHead>
                        <TableHead>Copies</TableHead>
                        <TableHead>Reason</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {printLogs.map((log, index) => (
                        <TableRow key={index} className="hover:bg-gray-50">
                          <TableCell>
                            <Badge className={log.action === 'reprint' ? 'badge-hold' : 'badge-available'}>
                              {log.action}
                            </Badge>
                          </TableCell>
                          <TableCell className="font-mono text-sm">{log.label_id}</TableCell>
                          <TableCell>{new Date(log.printed_at).toLocaleString()}</TableCell>
                          <TableCell>{log.printed_by_name}</TableCell>
                          <TableCell className="tabular-nums">{log.quantity_printed}</TableCell>
                          <TableCell className="max-w-xs truncate">{log.reason || '-'}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Labels;
