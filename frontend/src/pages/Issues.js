import React, { useState, useEffect } from 'react';
import { issueAPI, materialAPI, fifoLifoAPI } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription, DialogFooter } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  ArrowUpFromLine, Plus, Check, Trash2, Package, AlertTriangle, 
  Clock, Info, CheckCircle, XCircle, ArrowRight, RefreshCw,
  FileText, Timer, AlertCircle
} from 'lucide-react';
import { toast } from 'sonner';

const Issues = () => {
  const { hasPermission, user } = useAuth();
  const [issues, setIssues] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('pending');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('issues');
  
  // Form state
  const [formData, setFormData] = useState({
    department: '',
    requisition_number: '',
    remarks: '',
    items: []
  });
  const [newItem, setNewItem] = useState({ material_id: '', quantity: 1 });
  
  // FIFO/LIFO state
  const [recommendation, setRecommendation] = useState(null);
  const [loadingRecommendation, setLoadingRecommendation] = useState(false);
  const [selectedBatch, setSelectedBatch] = useState(null);
  const [showOverrideDialog, setShowOverrideDialog] = useState(false);
  const [overrideReason, setOverrideReason] = useState('');
  const [pendingItem, setPendingItem] = useState(null);
  
  // Exceptions state
  const [exceptions, setExceptions] = useState([]);
  const [exceptionSummary, setExceptionSummary] = useState(null);

  const canCreate = hasPermission(['Admin', 'Store In-Charge', 'Warehouse Operator']);
  const canViewExceptions = hasPermission(['Admin', 'Store In-Charge', 'Auditor', 'Inventory Controller']);

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  useEffect(() => {
    if (activeTab === 'exceptions' && canViewExceptions) {
      loadExceptions();
    }
  }, [activeTab]);

  const loadData = async () => {
    try {
      const [issuesRes, materialsRes] = await Promise.all([
        issueAPI.getAll(statusFilter !== 'all' ? { status: statusFilter } : {}),
        materialAPI.getAll()
      ]);
      setIssues(issuesRes.data);
      setMaterials(materialsRes.data.filter(m => m.current_stock > 0));
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadExceptions = async () => {
    try {
      const [exceptionsRes, summaryRes] = await Promise.all([
        fifoLifoAPI.getExceptions({ limit: 50 }),
        fifoLifoAPI.getExceptionSummary(30)
      ]);
      setExceptions(exceptionsRes.data.exceptions || []);
      setExceptionSummary(summaryRes.data);
    } catch (error) {
      console.error('Failed to load exceptions:', error);
    }
  };

  // Load FIFO/LIFO recommendation when material is selected
  const loadRecommendation = async (materialId, quantity) => {
    if (!materialId || quantity < 1) {
      setRecommendation(null);
      return;
    }
    
    setLoadingRecommendation(true);
    try {
      const response = await fifoLifoAPI.getRecommendation(materialId, quantity);
      setRecommendation(response.data);
      setSelectedBatch(null);
    } catch (error) {
      console.error('Failed to load recommendation:', error);
      setRecommendation(null);
    } finally {
      setLoadingRecommendation(false);
    }
  };

  // Handle material selection change
  const handleMaterialChange = (materialId) => {
    setNewItem({ ...newItem, material_id: materialId });
    if (materialId && newItem.quantity > 0) {
      loadRecommendation(materialId, newItem.quantity);
    }
  };

  // Handle quantity change
  const handleQuantityChange = (quantity) => {
    const qty = parseInt(quantity) || 0;
    setNewItem({ ...newItem, quantity: qty });
    if (newItem.material_id && qty > 0) {
      loadRecommendation(newItem.material_id, qty);
    }
  };

  // Handle batch selection
  const handleBatchSelect = async (batch) => {
    if (!recommendation) return;
    
    // Check if this follows FIFO/LIFO rules
    const recommendedBatch = recommendation.recommended_batches[0];
    
    if (recommendedBatch && batch.batch_number !== recommendedBatch.batch_number) {
      // User selected a different batch - need to validate
      setPendingItem({
        ...newItem,
        batch_number: batch.batch_number,
        bin_location: batch.bin_location
      });
      setSelectedBatch(batch);
      setShowOverrideDialog(true);
    } else {
      // Follows rules - proceed directly
      setSelectedBatch(batch);
      addItemWithBatch(batch);
    }
  };

  // Add item with selected batch
  const addItemWithBatch = (batch) => {
    const material = materials.find(m => m.material_id === newItem.material_id);
    if (!material) return;

    const pickQty = Math.min(newItem.quantity, batch.quantity);

    const existingIndex = formData.items.findIndex(
      i => i.material_id === newItem.material_id && i.batch_number === batch.batch_number
    );

    if (existingIndex >= 0) {
      const updatedItems = [...formData.items];
      updatedItems[existingIndex].quantity += pickQty;
      setFormData({ ...formData, items: updatedItems });
    } else {
      setFormData({
        ...formData,
        items: [...formData.items, {
          material_id: material.material_id,
          material_code: material.material_code,
          material_name: material.name,
          quantity: pickQty,
          batch_number: batch.batch_number,
          bin_location: batch.bin_location,
          stock_method: material.stock_method
        }]
      });
    }

    // Reset
    setNewItem({ material_id: '', quantity: 1 });
    setRecommendation(null);
    setSelectedBatch(null);
    toast.success(`Added ${pickQty} units from batch ${batch.batch_number}`);
  };

  // Handle override confirmation
  const handleOverrideConfirm = async () => {
    if (overrideReason.length < 10) {
      toast.error('Please provide a detailed reason (at least 10 characters)');
      return;
    }

    try {
      // Log the exception
      await fifoLifoAPI.logException({
        material_id: newItem.material_id,
        selected_batch: selectedBatch.batch_number,
        recommended_batch: recommendation.recommended_batches[0].batch_number,
        override_reason: overrideReason
      });

      toast.warning(`${recommendation.stock_method} override logged`);
      
      // Proceed with adding the item
      addItemWithBatch(selectedBatch);
      
      setShowOverrideDialog(false);
      setOverrideReason('');
      setPendingItem(null);
    } catch (error) {
      toast.error('Failed to log exception');
    }
  };

  const handleAddItem = () => {
    if (!newItem.material_id || newItem.quantity < 1) {
      toast.error('Select material and enter quantity');
      return;
    }
    
    const material = materials.find(m => m.material_id === newItem.material_id);
    if (!material) return;

    if (newItem.quantity > material.current_stock) {
      toast.error(`Only ${material.current_stock} available`);
      return;
    }

    // If we have a recommendation, user should select a batch
    if (recommendation && recommendation.recommended_batches.length > 0) {
      toast.info('Please select a batch from the recommendation below');
      return;
    }

    // No recommendation available - add directly
    const existingIndex = formData.items.findIndex(i => i.material_id === newItem.material_id);
    if (existingIndex >= 0) {
      const updatedItems = [...formData.items];
      updatedItems[existingIndex].quantity += newItem.quantity;
      setFormData({ ...formData, items: updatedItems });
    } else {
      setFormData({
        ...formData,
        items: [...formData.items, {
          material_id: material.material_id,
          material_code: material.material_code,
          material_name: material.name,
          quantity: newItem.quantity,
          stock_method: material.stock_method
        }]
      });
    }
    setNewItem({ material_id: '', quantity: 1 });
    setRecommendation(null);
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
    if (!formData.department) {
      toast.error('Enter department');
      return;
    }
    
    try {
      await issueAPI.create(formData);
      toast.success('Material issue created successfully');
      setIsDialogOpen(false);
      resetForm();
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create issue');
    }
  };

  const handleComplete = async (issue) => {
    try {
      await issueAPI.complete(issue.issue_id);
      toast.success('Issue completed - Stock updated');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to complete issue');
    }
  };

  const resetForm = () => {
    setFormData({
      department: '',
      requisition_number: '',
      remarks: '',
      items: []
    });
    setNewItem({ material_id: '', quantity: 1 });
    setRecommendation(null);
    setSelectedBatch(null);
  };

  const getMethodBadge = (method) => {
    return method === 'FIFO' 
      ? 'bg-blue-100 text-blue-700 border-blue-200'
      : 'bg-purple-100 text-purple-700 border-purple-200';
  };

  return (
    <div className="space-y-6">
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="flex flex-col sm:flex-row gap-4 justify-between">
          <TabsList>
            <TabsTrigger value="issues" data-testid="issues-tab">
              <ArrowUpFromLine className="w-4 h-4 mr-2" />
              Material Issues
            </TabsTrigger>
            {canViewExceptions && (
              <TabsTrigger value="exceptions" data-testid="exceptions-tab">
                <AlertTriangle className="w-4 h-4 mr-2" />
                FIFO/LIFO Exceptions
              </TabsTrigger>
            )}
          </TabsList>

          {activeTab === 'issues' && (
            <div className="flex gap-3">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-40" data-testid="issue-status-filter">
                  <SelectValue placeholder="Filter Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                </SelectContent>
              </Select>

              {canCreate && (
                <Dialog open={isDialogOpen} onOpenChange={(open) => { setIsDialogOpen(open); if (!open) resetForm(); }}>
                  <DialogTrigger asChild>
                    <Button className="bg-[#f59e0b] hover:bg-[#d97706]" data-testid="create-issue-btn">
                      <Plus className="w-4 h-4 mr-2" />
                      Create Issue
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                      <DialogTitle className="flex items-center gap-2">
                        <ArrowUpFromLine className="w-5 h-5" />
                        Create Material Issue
                      </DialogTitle>
                      <DialogDescription>
                        Issue materials following FIFO/LIFO rules configured at material level
                      </DialogDescription>
                    </DialogHeader>
                    <form onSubmit={handleSubmit} className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Department *</Label>
                          <Input
                            value={formData.department}
                            onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                            placeholder="e.g., Production"
                            required
                            data-testid="issue-department-input"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Requisition Number</Label>
                          <Input
                            value={formData.requisition_number}
                            onChange={(e) => setFormData({ ...formData, requisition_number: e.target.value })}
                            placeholder="Optional"
                            data-testid="issue-requisition-input"
                          />
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label>Remarks</Label>
                        <Input
                          value={formData.remarks}
                          onChange={(e) => setFormData({ ...formData, remarks: e.target.value })}
                          placeholder="Optional remarks"
                          data-testid="issue-remarks-input"
                        />
                      </div>

                      {/* Add Items with FIFO/LIFO */}
                      <div className="border rounded-lg p-4 space-y-4">
                        <Label className="text-base font-semibold">Add Items</Label>
                        <div className="flex gap-4">
                          <Select value={newItem.material_id} onValueChange={handleMaterialChange}>
                            <SelectTrigger className="flex-1" data-testid="issue-material-select">
                              <SelectValue placeholder="Select Material" />
                            </SelectTrigger>
                            <SelectContent>
                              {materials.map((mat) => (
                                <SelectItem key={mat.material_id} value={mat.material_id}>
                                  <div className="flex items-center gap-2">
                                    <span>{mat.material_code} - {mat.name}</span>
                                    <Badge className={`text-xs ${getMethodBadge(mat.stock_method)}`}>
                                      {mat.stock_method}
                                    </Badge>
                                    <span className="text-gray-500">(Avail: {mat.current_stock})</span>
                                  </div>
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <Input
                            type="number"
                            className="w-28"
                            value={newItem.quantity}
                            onChange={(e) => handleQuantityChange(e.target.value)}
                            min={1}
                            placeholder="Qty"
                            data-testid="issue-quantity-input"
                          />
                          {!recommendation && (
                            <Button type="button" onClick={handleAddItem} variant="outline" data-testid="issue-add-item-btn">
                              <Plus className="w-4 h-4" />
                            </Button>
                          )}
                        </div>

                        {/* FIFO/LIFO Recommendation Panel */}
                        {loadingRecommendation && (
                          <div className="flex items-center justify-center p-4 bg-gray-50 rounded-lg">
                            <RefreshCw className="w-5 h-5 animate-spin mr-2" />
                            Loading batch recommendations...
                          </div>
                        )}

                        {recommendation && !loadingRecommendation && (
                          <div className={`rounded-lg border-2 p-4 ${recommendation.stock_method === 'FIFO' ? 'border-blue-200 bg-blue-50/50' : 'border-purple-200 bg-purple-50/50'}`}>
                            <div className="flex items-center justify-between mb-3">
                              <div className="flex items-center gap-2">
                                <Timer className="w-5 h-5" />
                                <span className="font-semibold">{recommendation.stock_method} Recommendation</span>
                                <Badge className={getMethodBadge(recommendation.stock_method)}>
                                  {recommendation.rule_description}
                                </Badge>
                              </div>
                              <span className="text-sm text-gray-600">
                                Available: {recommendation.available_stock} | Needed: {recommendation.quantity_needed}
                              </span>
                            </div>

                            {!recommendation.can_fulfill && (
                              <div className="flex items-center gap-2 p-2 bg-red-100 text-red-700 rounded mb-3">
                                <AlertCircle className="w-4 h-4" />
                                Insufficient stock to fulfill request
                              </div>
                            )}

                            <div className="space-y-2">
                              <p className="text-sm font-medium text-gray-700">Select batch to issue:</p>
                              <div className="grid gap-2">
                                {recommendation.all_batches.map((batch, idx) => (
                                  <div
                                    key={batch.batch_number}
                                    onClick={() => handleBatchSelect(batch)}
                                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                                      batch.is_recommended 
                                        ? 'border-green-400 bg-green-50 hover:bg-green-100' 
                                        : 'border-gray-200 bg-white hover:bg-gray-50'
                                    } ${selectedBatch?.batch_number === batch.batch_number ? 'ring-2 ring-[#f59e0b]' : ''}`}
                                    data-testid={`batch-${batch.batch_number}`}
                                  >
                                    <div className="flex items-center justify-between">
                                      <div className="flex items-center gap-3">
                                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                                          batch.is_recommended ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-600'
                                        }`}>
                                          {idx + 1}
                                        </div>
                                        <div>
                                          <p className="font-mono font-medium">{batch.batch_number}</p>
                                          <p className="text-xs text-gray-500">
                                            GRN: {batch.grn_number} | Bin: {batch.bin_location || 'N/A'}
                                          </p>
                                        </div>
                                      </div>
                                      <div className="text-right">
                                        <p className="font-bold tabular-nums">{batch.quantity} units</p>
                                        <p className="text-xs text-gray-500">
                                          Received: {batch.receipt_date?.slice(0, 10) || 'N/A'}
                                        </p>
                                      </div>
                                      <div className="ml-4">
                                        {batch.is_recommended ? (
                                          <Badge className="bg-green-100 text-green-700">
                                            <CheckCircle className="w-3 h-3 mr-1" />
                                            Recommended
                                          </Badge>
                                        ) : (
                                          <Badge variant="outline" className="text-amber-600 border-amber-300">
                                            <AlertTriangle className="w-3 h-3 mr-1" />
                                            Override Required
                                          </Badge>
                                        )}
                                      </div>
                                    </div>
                                    {batch.expiry_date && (
                                      <p className="text-xs text-gray-500 mt-1 ml-11">
                                        Expiry: {batch.expiry_date.slice(0, 10)}
                                      </p>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Selected Items */}
                        {formData.items.length > 0 && (
                          <div className="space-y-2 mt-4">
                            <Label className="text-sm font-semibold text-gray-700">Selected Items:</Label>
                            {formData.items.map((item, index) => (
                              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border">
                                <div className="flex items-center gap-3">
                                  <Package className="w-5 h-5 text-gray-400" />
                                  <div>
                                    <p className="font-mono font-medium">{item.material_code}</p>
                                    <p className="text-sm text-gray-500">
                                      {item.material_name}
                                      {item.batch_number && <span className="ml-2">• Batch: {item.batch_number}</span>}
                                      {item.bin_location && <span className="ml-2">• Bin: {item.bin_location}</span>}
                                    </p>
                                  </div>
                                </div>
                                <div className="flex items-center gap-4">
                                  <Badge className={getMethodBadge(item.stock_method || 'FIFO')}>
                                    {item.stock_method || 'FIFO'}
                                  </Badge>
                                  <span className="font-bold tabular-nums text-lg">{item.quantity}</span>
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    className="text-red-600 hover:text-red-700"
                                    onClick={() => handleRemoveItem(index)}
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </Button>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>

                      <div className="flex justify-end gap-3 pt-4">
                        <Button type="button" variant="outline" onClick={() => { setIsDialogOpen(false); resetForm(); }}>
                          Cancel
                        </Button>
                        <Button type="submit" className="bg-[#f59e0b] hover:bg-[#d97706]" data-testid="issue-submit-btn">
                          Create Issue
                        </Button>
                      </div>
                    </form>
                  </DialogContent>
                </Dialog>
              )}
            </div>
          )}
        </div>

        {/* Issues Tab */}
        <TabsContent value="issues">
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[1, 2].map((i) => (
                <Card key={i} className="animate-pulse">
                  <CardContent className="pt-6">
                    <div className="h-40 bg-gray-200 rounded"></div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : issues.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <ArrowUpFromLine className="w-16 h-16 mx-auto mb-4 opacity-20" />
              <p className="text-lg">No material issues found</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {issues.map((issue) => (
                <Card key={issue.issue_id} className="border border-gray-200" data-testid={`issue-card-${issue.issue_number}`}>
                  <CardHeader className="pb-2">
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="text-base font-mono">{issue.issue_number}</CardTitle>
                        <p className="text-sm text-gray-500 mt-1">Dept: {issue.department}</p>
                      </div>
                      <Badge className={issue.status === 'pending' ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'}>
                        {issue.status}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      {issue.items.slice(0, 3).map((item, idx) => (
                        <div key={idx} className="flex justify-between items-center text-sm p-2 bg-gray-50 rounded">
                          <div className="flex items-center gap-2">
                            <span className="font-mono">{item.material_code}</span>
                            {item.batch_number && (
                              <span className="text-xs text-gray-500">({item.batch_number})</span>
                            )}
                          </div>
                          <span className="font-bold tabular-nums">{item.quantity}</span>
                        </div>
                      ))}
                      {issue.items.length > 3 && (
                        <p className="text-xs text-gray-500 text-center">+{issue.items.length - 3} more items</p>
                      )}
                    </div>

                    <div className="flex justify-between items-center text-sm text-gray-600">
                      <span>Total: <strong className="text-gray-900">{issue.total_quantity}</strong> units</span>
                      <span>{new Date(issue.created_at).toLocaleDateString()}</span>
                    </div>

                    {issue.status === 'pending' && canCreate && (
                      <Button
                        onClick={() => handleComplete(issue)}
                        className="w-full bg-green-600 hover:bg-green-700"
                        data-testid={`complete-issue-${issue.issue_number}`}
                      >
                        <Check className="w-5 h-5 mr-2" />
                        Complete Issue
                      </Button>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* FIFO/LIFO Exceptions Tab */}
        {canViewExceptions && (
          <TabsContent value="exceptions" className="space-y-6">
            {/* Summary Cards */}
            {exceptionSummary && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="border-l-4 border-l-amber-500">
                  <CardContent className="pt-4">
                    <p className="text-xs text-gray-500 uppercase">Total Exceptions (30d)</p>
                    <p className="text-3xl font-bold">{exceptionSummary.total_exceptions}</p>
                  </CardContent>
                </Card>
                <Card className="border-l-4 border-l-blue-500">
                  <CardContent className="pt-4">
                    <p className="text-xs text-gray-500 uppercase">FIFO Overrides</p>
                    <p className="text-3xl font-bold text-blue-600">{exceptionSummary.by_method?.FIFO || 0}</p>
                  </CardContent>
                </Card>
                <Card className="border-l-4 border-l-purple-500">
                  <CardContent className="pt-4">
                    <p className="text-xs text-gray-500 uppercase">LIFO Overrides</p>
                    <p className="text-3xl font-bold text-purple-600">{exceptionSummary.by_method?.LIFO || 0}</p>
                  </CardContent>
                </Card>
                <Card className="border-l-4 border-l-gray-500">
                  <CardContent className="pt-4">
                    <p className="text-xs text-gray-500 uppercase">Top Material</p>
                    <p className="text-lg font-mono font-bold truncate">
                      {exceptionSummary.top_materials?.[0]?._id || 'N/A'}
                    </p>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Exceptions Table */}
            <Card className="border border-gray-200">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-amber-500" />
                  FIFO/LIFO Exception Log
                </CardTitle>
                <CardDescription>
                  All instances where users bypassed FIFO/LIFO recommendations
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                {exceptions.length === 0 ? (
                  <div className="p-8 text-center text-gray-500">
                    <CheckCircle className="w-12 h-12 mx-auto mb-3 opacity-20" />
                    <p>No exceptions found - Great compliance!</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="bg-gray-50">
                          <TableHead className="font-semibold">Date</TableHead>
                          <TableHead className="font-semibold">Material</TableHead>
                          <TableHead className="font-semibold">Method</TableHead>
                          <TableHead className="font-semibold">Recommended</TableHead>
                          <TableHead className="font-semibold">Selected</TableHead>
                          <TableHead className="font-semibold">Override Reason</TableHead>
                          <TableHead className="font-semibold">User</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {exceptions.map((exc) => (
                          <TableRow key={exc.exception_id} className="hover:bg-gray-50">
                            <TableCell className="text-sm">
                              {new Date(exc.created_at).toLocaleString()}
                            </TableCell>
                            <TableCell className="font-mono font-medium">{exc.material_code}</TableCell>
                            <TableCell>
                              <Badge className={getMethodBadge(exc.stock_method)}>
                                {exc.stock_method}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <div>
                                <p className="font-mono text-sm">{exc.recommended_batch}</p>
                                <p className="text-xs text-gray-500">{exc.recommended_receipt_date?.slice(0, 10)}</p>
                              </div>
                            </TableCell>
                            <TableCell>
                              <div>
                                <p className="font-mono text-sm text-amber-600">{exc.selected_batch}</p>
                                <p className="text-xs text-gray-500">{exc.selected_receipt_date?.slice(0, 10)}</p>
                              </div>
                            </TableCell>
                            <TableCell className="max-w-xs">
                              <p className="text-sm truncate" title={exc.override_reason}>
                                {exc.override_reason}
                              </p>
                            </TableCell>
                            <TableCell className="text-sm">{exc.created_by_name}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>

      {/* Override Confirmation Dialog */}
      <Dialog open={showOverrideDialog} onOpenChange={setShowOverrideDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-amber-600">
              <AlertTriangle className="w-5 h-5" />
              {recommendation?.stock_method} Rule Override
            </DialogTitle>
            <DialogDescription>
              You are selecting a batch that does not follow {recommendation?.stock_method} rules
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <p className="text-sm text-amber-800">
                <strong>Warning:</strong> {recommendation?.stock_method === 'FIFO' 
                  ? 'Older stock should be issued first to maintain FIFO compliance.'
                  : 'Newer stock should be issued first to maintain LIFO compliance.'}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                <p className="text-xs text-gray-500 uppercase mb-1">Recommended Batch</p>
                <p className="font-mono font-bold text-green-700">
                  {recommendation?.recommended_batches?.[0]?.batch_number}
                </p>
                <p className="text-xs text-gray-600">
                  Received: {recommendation?.recommended_batches?.[0]?.receipt_date?.slice(0, 10)}
                </p>
              </div>
              <div className="p-3 bg-amber-50 rounded-lg border border-amber-200">
                <p className="text-xs text-gray-500 uppercase mb-1">Your Selection</p>
                <p className="font-mono font-bold text-amber-700">
                  {selectedBatch?.batch_number}
                </p>
                <p className="text-xs text-gray-600">
                  Received: {selectedBatch?.receipt_date?.slice(0, 10)}
                </p>
              </div>
            </div>

            <div className="space-y-2">
              <Label className="font-semibold">Override Reason (Required) *</Label>
              <Textarea
                value={overrideReason}
                onChange={(e) => setOverrideReason(e.target.value)}
                placeholder="Please provide a detailed reason for bypassing the FIFO/LIFO rule (min 10 characters)"
                className="min-h-[100px]"
                data-testid="override-reason-input"
              />
              <p className="text-xs text-gray-500">
                This exception will be logged and visible in audit reports
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowOverrideDialog(false); setOverrideReason(''); }}>
              Cancel
            </Button>
            <Button 
              onClick={handleOverrideConfirm}
              className="bg-amber-600 hover:bg-amber-700"
              disabled={overrideReason.length < 10}
              data-testid="confirm-override-btn"
            >
              Confirm Override
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Issues;
