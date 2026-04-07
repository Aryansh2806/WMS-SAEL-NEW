import React, { useState, useEffect } from 'react';
import { grnAPI, materialAPI, binAPI } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Plus, FileInput, Check, Eye, Trash2, ClipboardCheck, Package, Calendar, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';

const QUALITY_STATUS = ['pending', 'passed', 'failed', 'partial'];
const STORAGE_CONDITIONS = ['ambient', 'cold_storage', 'frozen', 'controlled_temperature', 'humidity_controlled', 'hazardous'];

const GRN = () => {
  const { hasPermission } = useAuth();
  const [grns, setGrns] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [bins, setBins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isViewDialogOpen, setIsViewDialogOpen] = useState(false);
  const [isInspectDialogOpen, setIsInspectDialogOpen] = useState(false);
  const [viewingGRN, setViewingGRN] = useState(null);
  const [inspectingGRN, setInspectingGRN] = useState(null);
  
  // Form state
  const [formData, setFormData] = useState({
    vendor_name: '',
    po_number: '',
    invoice_number: '',
    receipt_date: '',
    remarks: '',
    items: []
  });
  
  // New item state
  const [newItem, setNewItem] = useState({
    material_id: '',
    received_quantity: 1,
    accepted_quantity: 0,
    rejected_quantity: 0,
    batch_number: '',
    manufacturing_date: '',
    expiry_date: '',
    quality_inspection_status: 'pending',
    storage_condition: 'ambient',
    bin_location: '',
    rejection_reason: ''
  });
  
  // Inspection updates state
  const [inspectionUpdates, setInspectionUpdates] = useState([]);

  const canCreate = hasPermission(['Admin', 'Store In-Charge', 'Warehouse Operator']);
  const canComplete = hasPermission(['Admin', 'Store In-Charge']);
  const canInspect = hasPermission(['Admin', 'Store In-Charge', 'Inventory Controller']);

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  const loadData = async () => {
    try {
      const [grnsRes, materialsRes, binsRes] = await Promise.all([
        grnAPI.getAll(statusFilter !== 'all' ? { status: statusFilter } : {}),
        materialAPI.getAll(),
        binAPI.getAll()
      ]);
      setGrns(grnsRes.data);
      setMaterials(materialsRes.data);
      setBins(binsRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleAddItem = () => {
    if (!newItem.material_id || newItem.received_quantity < 1) {
      toast.error('Select material and enter received quantity');
      return;
    }
    
    const material = materials.find(m => m.material_id === newItem.material_id);
    if (!material) return;

    // Check if material already added
    if (formData.items.some(i => i.material_id === newItem.material_id && i.batch_number === newItem.batch_number)) {
      toast.error('This material with same batch already added. Use different batch number.');
      return;
    }

    setFormData({
      ...formData,
      items: [...formData.items, {
        ...newItem,
        material_code: material.material_code,
        material_name: material.name
      }]
    });
    
    // Reset new item form
    setNewItem({
      material_id: '',
      received_quantity: 1,
      accepted_quantity: 0,
      rejected_quantity: 0,
      batch_number: '',
      manufacturing_date: '',
      expiry_date: '',
      quality_inspection_status: 'pending',
      storage_condition: 'ambient',
      bin_location: '',
      rejection_reason: ''
    });
  };

  const handleRemoveItem = (index) => {
    setFormData({
      ...formData,
      items: formData.items.filter((_, i) => i !== index)
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (formData.items.length === 0) {
      toast.error('Add at least one item');
      return;
    }
    if (!formData.vendor_name) {
      toast.error('Enter vendor name');
      return;
    }
    
    try {
      await grnAPI.create(formData);
      toast.success('GRN created successfully');
      setIsCreateDialogOpen(false);
      resetForm();
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create GRN');
    }
  };

  const handleComplete = async (grn) => {
    // Check if already completed
    if (grn.status === 'completed') {
      toast.info('This GRN is already completed');
      return;
    }
    
    // Check if all items are inspected
    const hasPending = grn.items.some(item => 
      item.quality_inspection_status === 'pending' && item.pending_quantity > 0
    );
    
    if (hasPending) {
      toast.error('Complete quality inspection for all items first');
      return;
    }
    
    if (!window.confirm(`Complete this GRN? Stock will be updated with ${grn.total_accepted_quantity} accepted units.`)) {
      return;
    }
    
    try {
      const result = await grnAPI.complete(grn.grn_id);
      toast.success(`GRN completed successfully!`);
      loadData();
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to complete GRN';
      if (errorMsg.includes('already completed')) {
        toast.info('This GRN is already completed. Stock has been updated.');
        loadData(); // Refresh to show updated status
      } else {
        toast.error(errorMsg);
      }
    }
  };

  const openInspectionDialog = (grn) => {
    setInspectingGRN(grn);
    setInspectionUpdates(grn.items.map(item => ({
      item_id: item.item_id,
      accepted_quantity: item.accepted_quantity,
      rejected_quantity: item.rejected_quantity,
      quality_inspection_status: item.quality_inspection_status,
      rejection_reason: item.rejection_reason || '',
      bin_location: item.bin_location || ''
    })));
    setIsInspectDialogOpen(true);
  };

  const handleInspectionUpdate = (itemId, field, value) => {
    setInspectionUpdates(prev => prev.map(item => {
      if (item.item_id === itemId) {
        const updated = { ...item, [field]: value };
        
        // Auto-calculate quantities
        const grnItem = inspectingGRN.items.find(i => i.item_id === itemId);
        if (field === 'accepted_quantity') {
          updated.rejected_quantity = Math.max(0, grnItem.received_quantity - parseInt(value || 0));
        } else if (field === 'rejected_quantity') {
          updated.accepted_quantity = Math.max(0, grnItem.received_quantity - parseInt(value || 0));
        }
        
        // Auto-update status based on quantities
        if (parseInt(updated.accepted_quantity) === grnItem.received_quantity) {
          updated.quality_inspection_status = 'passed';
        } else if (parseInt(updated.rejected_quantity) === grnItem.received_quantity) {
          updated.quality_inspection_status = 'failed';
        } else if (parseInt(updated.accepted_quantity) > 0 && parseInt(updated.rejected_quantity) > 0) {
          updated.quality_inspection_status = 'partial';
        }
        
        return updated;
      }
      return item;
    }));
  };

  const handleSaveInspection = async () => {
    try {
      await grnAPI.updateInspection(inspectingGRN.grn_id, inspectionUpdates);
      toast.success('Inspection updated successfully');
      setIsInspectDialogOpen(false);
      setInspectingGRN(null);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update inspection');
    }
  };

  const resetForm = () => {
    setFormData({
      vendor_name: '',
      po_number: '',
      invoice_number: '',
      receipt_date: '',
      remarks: '',
      items: []
    });
    setNewItem({
      material_id: '',
      received_quantity: 1,
      accepted_quantity: 0,
      rejected_quantity: 0,
      batch_number: '',
      manufacturing_date: '',
      expiry_date: '',
      quality_inspection_status: 'pending',
      storage_condition: 'ambient',
      bin_location: '',
      rejection_reason: ''
    });
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'pending': return <Badge className="badge-pending">Pending</Badge>;
      case 'partial': return <Badge className="badge-hold">Partial</Badge>;
      case 'completed': return <Badge className="badge-completed">Completed</Badge>;
      case 'cancelled': return <Badge className="badge-blocked">Cancelled</Badge>;
      default: return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getQualityBadge = (status) => {
    switch (status) {
      case 'passed': return <Badge className="badge-available">Passed</Badge>;
      case 'failed': return <Badge className="badge-blocked">Failed</Badge>;
      case 'partial': return <Badge className="badge-hold">Partial</Badge>;
      case 'pending': return <Badge className="badge-pending">Pending</Badge>;
      default: return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between">
        <div className="flex gap-4">
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-48" data-testid="grn-status-filter">
              <SelectValue placeholder="All Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="partial">Partial</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {canCreate && (
          <Dialog open={isCreateDialogOpen} onOpenChange={(open) => { setIsCreateDialogOpen(open); if (!open) resetForm(); }}>
            <DialogTrigger asChild>
              <Button className="bg-[#f59e0b] hover:bg-[#d97706]" data-testid="create-grn-btn">
                <Plus className="w-4 h-4 mr-2" />
                Create GRN
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create Goods Receipt Note (GRN)</DialogTitle>
                <DialogDescription>Enter receipt details and add materials received from vendor.</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Header Info */}
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Vendor Name *</Label>
                    <Input
                      value={formData.vendor_name}
                      onChange={(e) => setFormData({ ...formData, vendor_name: e.target.value })}
                      placeholder="Enter vendor name"
                      required
                      data-testid="grn-vendor-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>PO Number</Label>
                    <Input
                      value={formData.po_number}
                      onChange={(e) => setFormData({ ...formData, po_number: e.target.value })}
                      placeholder="Purchase Order #"
                      data-testid="grn-po-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Invoice Number</Label>
                    <Input
                      value={formData.invoice_number}
                      onChange={(e) => setFormData({ ...formData, invoice_number: e.target.value })}
                      placeholder="Invoice #"
                      data-testid="grn-invoice-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Receipt Date</Label>
                    <Input
                      type="datetime-local"
                      value={formData.receipt_date}
                      onChange={(e) => setFormData({ ...formData, receipt_date: e.target.value })}
                      data-testid="grn-receipt-date-input"
                    />
                  </div>
                  <div className="col-span-2 space-y-2">
                    <Label>Remarks</Label>
                    <Input
                      value={formData.remarks}
                      onChange={(e) => setFormData({ ...formData, remarks: e.target.value })}
                      placeholder="Optional remarks"
                      data-testid="grn-remarks-input"
                    />
                  </div>
                </div>

                {/* Add Item Section */}
                <Card className="border-dashed">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <Package className="w-5 h-5" />
                      Add Material Item
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="col-span-2 space-y-2">
                        <Label>Material *</Label>
                        <Select value={newItem.material_id} onValueChange={(v) => setNewItem({ ...newItem, material_id: v })}>
                          <SelectTrigger data-testid="grn-material-select">
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
                        <Label>Received Qty *</Label>
                        <Input
                          type="number"
                          value={newItem.received_quantity}
                          onChange={(e) => setNewItem({ ...newItem, received_quantity: parseInt(e.target.value) || 0 })}
                          min={1}
                          data-testid="grn-received-qty-input"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Batch/Lot Number</Label>
                        <Input
                          value={newItem.batch_number}
                          onChange={(e) => setNewItem({ ...newItem, batch_number: e.target.value })}
                          placeholder="Auto-generated if empty"
                          data-testid="grn-batch-input"
                        />
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="space-y-2">
                        <Label>Manufacturing Date</Label>
                        <Input
                          type="date"
                          value={newItem.manufacturing_date}
                          onChange={(e) => setNewItem({ ...newItem, manufacturing_date: e.target.value })}
                          data-testid="grn-mfg-date-input"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Expiry Date</Label>
                        <Input
                          type="date"
                          value={newItem.expiry_date}
                          onChange={(e) => setNewItem({ ...newItem, expiry_date: e.target.value })}
                          data-testid="grn-expiry-date-input"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Storage Condition</Label>
                        <Select value={newItem.storage_condition} onValueChange={(v) => setNewItem({ ...newItem, storage_condition: v })}>
                          <SelectTrigger data-testid="grn-storage-select">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {STORAGE_CONDITIONS.map((cond) => (
                              <SelectItem key={cond} value={cond} className="capitalize">
                                {cond.replace(/_/g, ' ')}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label>Bin Location</Label>
                        <Select value={newItem.bin_location || 'none'} onValueChange={(v) => setNewItem({ ...newItem, bin_location: v === 'none' ? '' : v })}>
                          <SelectTrigger data-testid="grn-bin-select">
                            <SelectValue placeholder="Select Bin" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="none">None</SelectItem>
                            {bins.filter(b => b.status !== 'blocked').map((bin) => (
                              <SelectItem key={bin.bin_id} value={bin.bin_code}>
                                {bin.bin_code} ({bin.status})
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    
                    <Button type="button" onClick={handleAddItem} variant="outline" className="w-full" data-testid="grn-add-item-btn">
                      <Plus className="w-4 h-4 mr-2" />
                      Add Item to GRN
                    </Button>
                  </CardContent>
                </Card>

                {/* Items List */}
                {formData.items.length > 0 && (
                  <div className="border rounded-lg overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow className="bg-gray-50">
                          <TableHead>Material</TableHead>
                          <TableHead>Batch #</TableHead>
                          <TableHead className="text-right">Received</TableHead>
                          <TableHead>Mfg Date</TableHead>
                          <TableHead>Expiry</TableHead>
                          <TableHead>Storage</TableHead>
                          <TableHead className="w-16"></TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {formData.items.map((item, index) => (
                          <TableRow key={index}>
                            <TableCell>
                              <div>
                                <span className="font-mono font-medium">{item.material_code}</span>
                                <p className="text-xs text-gray-500">{item.material_name}</p>
                              </div>
                            </TableCell>
                            <TableCell className="font-mono text-sm">{item.batch_number || 'Auto'}</TableCell>
                            <TableCell className="text-right tabular-nums font-medium">{item.received_quantity}</TableCell>
                            <TableCell className="text-sm">{item.manufacturing_date || '-'}</TableCell>
                            <TableCell className="text-sm">
                              {item.expiry_date ? (
                                <span className={new Date(item.expiry_date) < new Date() ? 'text-red-600' : ''}>
                                  {item.expiry_date}
                                </span>
                              ) : '-'}
                            </TableCell>
                            <TableCell className="capitalize text-sm">{item.storage_condition?.replace(/_/g, ' ')}</TableCell>
                            <TableCell>
                              <Button
                                type="button"
                                variant="ghost"
                                size="sm"
                                className="text-red-600"
                                onClick={() => handleRemoveItem(index)}
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}

                <div className="flex justify-between items-center pt-4 border-t">
                  <div className="text-sm text-gray-600">
                    Total Items: <strong>{formData.items.length}</strong> | 
                    Total Qty: <strong className="tabular-nums">{formData.items.reduce((sum, i) => sum + i.received_quantity, 0)}</strong>
                  </div>
                  <div className="flex gap-3">
                    <Button type="button" variant="outline" onClick={() => { setIsCreateDialogOpen(false); resetForm(); }}>
                      Cancel
                    </Button>
                    <Button type="submit" className="bg-[#f59e0b] hover:bg-[#d97706]" data-testid="grn-submit-btn">
                      Create GRN
                    </Button>
                  </div>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* View GRN Dialog */}
      <Dialog open={isViewDialogOpen} onOpenChange={setIsViewDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>GRN Details - {viewingGRN?.grn_number}</DialogTitle>
          </DialogHeader>
          {viewingGRN && (
            <div className="space-y-6">
              {/* Header Info */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div><span className="text-gray-500">Vendor:</span><br/><strong>{viewingGRN.vendor_name}</strong></div>
                <div><span className="text-gray-500">PO Number:</span><br/><strong>{viewingGRN.po_number || '-'}</strong></div>
                <div><span className="text-gray-500">Invoice:</span><br/><strong>{viewingGRN.invoice_number || '-'}</strong></div>
                <div><span className="text-gray-500">Status:</span><br/>{getStatusBadge(viewingGRN.status)}</div>
                <div><span className="text-gray-500">Receipt Date:</span><br/><strong>{new Date(viewingGRN.receipt_date).toLocaleString()}</strong></div>
                <div><span className="text-gray-500">Received By:</span><br/><strong>{viewingGRN.receiving_user_name}</strong></div>
                <div><span className="text-gray-500">Total Received:</span><br/><strong className="tabular-nums">{viewingGRN.total_received_quantity}</strong></div>
                <div>
                  <span className="text-gray-500">Accepted/Rejected:</span><br/>
                  <strong className="text-green-600 tabular-nums">{viewingGRN.total_accepted_quantity}</strong>
                  <span className="text-gray-400"> / </span>
                  <strong className="text-red-600 tabular-nums">{viewingGRN.total_rejected_quantity}</strong>
                </div>
              </div>
              
              {/* Items */}
              <div className="border rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-gray-50">
                      <TableHead>Material</TableHead>
                      <TableHead>Batch #</TableHead>
                      <TableHead className="text-right">Received</TableHead>
                      <TableHead className="text-right">Accepted</TableHead>
                      <TableHead className="text-right">Rejected</TableHead>
                      <TableHead>Expiry</TableHead>
                      <TableHead>QC Status</TableHead>
                      <TableHead>Bin</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {viewingGRN.items.map((item, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <div>
                            <span className="font-mono font-medium">{item.material_code}</span>
                            <p className="text-xs text-gray-500">{item.material_name}</p>
                          </div>
                        </TableCell>
                        <TableCell className="font-mono text-sm">{item.batch_number}</TableCell>
                        <TableCell className="text-right tabular-nums">{item.received_quantity}</TableCell>
                        <TableCell className="text-right tabular-nums text-green-600 font-medium">{item.accepted_quantity}</TableCell>
                        <TableCell className="text-right tabular-nums text-red-600 font-medium">{item.rejected_quantity}</TableCell>
                        <TableCell className="text-sm">
                          {item.expiry_date ? (
                            <span className={new Date(item.expiry_date) < new Date() ? 'text-red-600 flex items-center gap-1' : ''}>
                              {new Date(item.expiry_date) < new Date() && <AlertTriangle className="w-3 h-3" />}
                              {item.expiry_date}
                            </span>
                          ) : '-'}
                        </TableCell>
                        <TableCell>{getQualityBadge(item.quality_inspection_status)}</TableCell>
                        <TableCell className="font-mono text-sm">{item.bin_location || '-'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {viewingGRN.remarks && (
                <div className="p-3 bg-gray-50 rounded-lg text-sm">
                  <span className="text-gray-500">Remarks:</span> {viewingGRN.remarks}
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Inspection Dialog */}
      <Dialog open={isInspectDialogOpen} onOpenChange={setIsInspectDialogOpen}>
        <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ClipboardCheck className="w-5 h-5" />
              Quality Inspection - {inspectingGRN?.grn_number}
            </DialogTitle>
            <DialogDescription>Update accepted/rejected quantities and inspection status for each item.</DialogDescription>
          </DialogHeader>
          {inspectingGRN && (
            <div className="space-y-4">
              <div className="border rounded-lg overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-gray-50">
                      <TableHead>Material</TableHead>
                      <TableHead>Batch</TableHead>
                      <TableHead className="text-right">Received</TableHead>
                      <TableHead className="text-right">Accepted</TableHead>
                      <TableHead className="text-right">Rejected</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Bin Location</TableHead>
                      <TableHead>Rejection Reason</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {inspectingGRN.items.map((item, index) => {
                      const update = inspectionUpdates.find(u => u.item_id === item.item_id) || {};
                      return (
                        <TableRow key={index}>
                          <TableCell>
                            <div>
                              <span className="font-mono font-medium">{item.material_code}</span>
                              <p className="text-xs text-gray-500">{item.material_name}</p>
                            </div>
                          </TableCell>
                          <TableCell className="font-mono text-sm">{item.batch_number}</TableCell>
                          <TableCell className="text-right tabular-nums font-medium">{item.received_quantity}</TableCell>
                          <TableCell>
                            <Input
                              type="number"
                              className="w-20 text-right"
                              value={update.accepted_quantity || 0}
                              onChange={(e) => handleInspectionUpdate(item.item_id, 'accepted_quantity', e.target.value)}
                              min={0}
                              max={item.received_quantity}
                            />
                          </TableCell>
                          <TableCell>
                            <Input
                              type="number"
                              className="w-20 text-right"
                              value={update.rejected_quantity || 0}
                              onChange={(e) => handleInspectionUpdate(item.item_id, 'rejected_quantity', e.target.value)}
                              min={0}
                              max={item.received_quantity}
                            />
                          </TableCell>
                          <TableCell>
                            <Select
                              value={update.quality_inspection_status || 'pending'}
                              onValueChange={(v) => handleInspectionUpdate(item.item_id, 'quality_inspection_status', v)}
                            >
                              <SelectTrigger className="w-28">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {QUALITY_STATUS.map((status) => (
                                  <SelectItem key={status} value={status} className="capitalize">{status}</SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </TableCell>
                          <TableCell>
                            <Select
                              value={update.bin_location || 'none'}
                              onValueChange={(v) => handleInspectionUpdate(item.item_id, 'bin_location', v === 'none' ? '' : v)}
                            >
                              <SelectTrigger className="w-28">
                                <SelectValue placeholder="Select" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="none">None</SelectItem>
                                {bins.filter(b => b.status !== 'blocked').map((bin) => (
                                  <SelectItem key={bin.bin_id} value={bin.bin_code}>{bin.bin_code}</SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </TableCell>
                          <TableCell>
                            <Input
                              className="w-32"
                              placeholder="Reason..."
                              value={update.rejection_reason || ''}
                              onChange={(e) => handleInspectionUpdate(item.item_id, 'rejection_reason', e.target.value)}
                            />
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>

              <div className="flex justify-end gap-3">
                <Button variant="outline" onClick={() => setIsInspectDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleSaveInspection} className="bg-[#f59e0b] hover:bg-[#d97706]">
                  Save Inspection Results
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* GRN Table */}
      <Card className="border border-gray-200">
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-gray-500">Loading GRNs...</div>
          ) : grns.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <FileInput className="w-12 h-12 mx-auto mb-2 opacity-20" />
              <p>No GRNs found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-gray-50">
                    <TableHead className="font-semibold">GRN Number</TableHead>
                    <TableHead className="font-semibold">Vendor</TableHead>
                    <TableHead className="font-semibold">PO #</TableHead>
                    <TableHead className="font-semibold text-right">Items</TableHead>
                    <TableHead className="font-semibold text-right">Received</TableHead>
                    <TableHead className="font-semibold text-right">Accepted</TableHead>
                    <TableHead className="font-semibold text-right">Rejected</TableHead>
                    <TableHead className="font-semibold">Status</TableHead>
                    <TableHead className="font-semibold">Receipt Date</TableHead>
                    <TableHead className="font-semibold text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {grns.map((grn) => (
                    <TableRow key={grn.grn_id} className="hover:bg-gray-50" data-testid={`grn-row-${grn.grn_number}`}>
                      <TableCell className="font-mono font-medium">{grn.grn_number}</TableCell>
                      <TableCell>{grn.vendor_name}</TableCell>
                      <TableCell>{grn.po_number || '-'}</TableCell>
                      <TableCell className="text-right tabular-nums">{grn.items?.length || 0}</TableCell>
                      <TableCell className="text-right tabular-nums">{grn.total_received_quantity}</TableCell>
                      <TableCell className="text-right tabular-nums text-green-600 font-medium">{grn.total_accepted_quantity}</TableCell>
                      <TableCell className="text-right tabular-nums text-red-600 font-medium">{grn.total_rejected_quantity}</TableCell>
                      <TableCell>{getStatusBadge(grn.status)}</TableCell>
                      <TableCell>{new Date(grn.receipt_date || grn.created_at).toLocaleDateString()}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => { setViewingGRN(grn); setIsViewDialogOpen(true); }}
                            data-testid={`view-grn-${grn.grn_number}`}
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          {canInspect && grn.status !== 'completed' && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-blue-600"
                              onClick={() => openInspectionDialog(grn)}
                              data-testid={`inspect-grn-${grn.grn_number}`}
                            >
                              <ClipboardCheck className="w-4 h-4" />
                            </Button>
                          )}
                          {canComplete && grn.status !== 'completed' && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-green-600 hover:text-green-700"
                              onClick={() => handleComplete(grn)}
                              data-testid={`complete-grn-${grn.grn_number}`}
                              title="Complete GRN and update stock"
                            >
                              <Check className="w-4 h-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default GRN;
