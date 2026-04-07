import React, { useState, useEffect } from 'react';
import { putawayAPI, grnAPI, materialAPI, binAPI } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Input } from '../components/ui/input';
import { ArrowDownToLine, Plus, Check, Package, MapPin } from 'lucide-react';
import { toast } from 'sonner';

const Putaway = () => {
  const { hasPermission } = useAuth();
  const [putaways, setPutaways] = useState([]);
  const [pendingGRNs, setPendingGRNs] = useState([]);
  const [bins, setBins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('pending');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedGRN, setSelectedGRN] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [selectedBin, setSelectedBin] = useState('');
  const [quantity, setQuantity] = useState(0);

  const canCreate = hasPermission(['Admin', 'Store In-Charge', 'Warehouse Operator']);

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  const loadData = async () => {
    try {
      const [putawaysRes, grnsRes, binsRes] = await Promise.all([
        putawayAPI.getAll(statusFilter !== 'all' ? { status: statusFilter } : {}),
        grnAPI.getAll({ status: 'completed' }), // Changed from 'pending' to 'completed'
        binAPI.getAll()
      ]);
      setPutaways(putawaysRes.data);
      setPendingGRNs(grnsRes.data);
      setBins(binsRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectGRN = (grn) => {
    setSelectedGRN(grn);
    setSelectedItem(null);
    setSelectedBin('');
    setQuantity(0);
  };

  const handleSelectItem = (item) => {
    setSelectedItem(item);
    setQuantity(item.quantity);
  };

  const handleSubmit = async () => {
    if (!selectedGRN || !selectedItem || !selectedBin || quantity < 1) {
      toast.error('Please fill all fields');
      return;
    }

    try {
      await putawayAPI.create({
        grn_id: selectedGRN.grn_id,
        material_id: selectedItem.material_id,
        quantity: quantity,
        bin_id: selectedBin
      });
      toast.success('Putaway created successfully');
      setIsDialogOpen(false);
      resetForm();
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create putaway');
    }
  };

  const handleComplete = async (putaway) => {
    try {
      await putawayAPI.complete(putaway.putaway_id);
      toast.success('Putaway completed');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to complete putaway');
    }
  };

  const resetForm = () => {
    setSelectedGRN(null);
    setSelectedItem(null);
    setSelectedBin('');
    setQuantity(0);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between">
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-48" data-testid="putaway-status-filter">
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
              <Button className="bg-[#f59e0b] hover:bg-[#d97706] touch-btn" data-testid="create-putaway-btn">
                <Plus className="w-4 h-4 mr-2" />
                Create Putaway
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create Putaway</DialogTitle>
              </DialogHeader>
              <div className="space-y-6">
                {/* Step 1: Select GRN */}
                <div className="space-y-3">
                  <Label className="text-base font-semibold">1. Select GRN (Completed & Ready for Putaway)</Label>
                  {pendingGRNs.length === 0 ? (
                    <p className="text-gray-500 text-sm">No completed GRNs available for putaway. Complete quality inspection first.</p>
                  ) : (
                    <div className="grid gap-2">
                      {pendingGRNs.map((grn) => (
                        <div
                          key={grn.grn_id}
                          onClick={() => handleSelectGRN(grn)}
                          className={`p-4 border rounded-lg cursor-pointer transition-all ${
                            selectedGRN?.grn_id === grn.grn_id
                              ? 'border-[#f59e0b] bg-amber-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                          data-testid={`select-grn-${grn.grn_number}`}
                        >
                          <div className="flex justify-between items-center">
                            <div>
                              <p className="font-mono font-medium">{grn.grn_number}</p>
                              <p className="text-sm text-gray-500">{grn.supplier_name}</p>
                            </div>
                            <Badge className="badge-pending">{grn.items.length} items</Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Step 2: Select Item */}
                {selectedGRN && (
                  <div className="space-y-3">
                    <Label className="text-base font-semibold">2. Select Item</Label>
                    <div className="grid gap-2">
                      {selectedGRN.items.map((item, idx) => (
                        <div
                          key={idx}
                          onClick={() => handleSelectItem(item)}
                          className={`p-4 border rounded-lg cursor-pointer transition-all ${
                            selectedItem?.material_id === item.material_id
                              ? 'border-[#f59e0b] bg-amber-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                          data-testid={`select-item-${item.material_code}`}
                        >
                          <div className="flex justify-between items-center">
                            <div className="flex items-center gap-3">
                              <Package className="w-5 h-5 text-gray-400" />
                              <div>
                                <p className="font-mono font-medium">{item.material_code}</p>
                                <p className="text-sm text-gray-500">{item.material_name}</p>
                              </div>
                            </div>
                            <span className="tabular-nums font-medium">{item.quantity} units</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Step 3: Select Bin & Quantity */}
                {selectedItem && (
                  <div className="space-y-3">
                    <Label className="text-base font-semibold">3. Assign Bin Location</Label>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Bin Location *</Label>
                        <Select value={selectedBin} onValueChange={setSelectedBin}>
                          <SelectTrigger className="touch-input" data-testid="putaway-bin-select">
                            <SelectValue placeholder="Select Bin" />
                          </SelectTrigger>
                          <SelectContent>
                            {bins.map((bin) => (
                              <SelectItem key={bin.bin_id} value={bin.bin_id}>
                                <div className="flex items-center gap-2">
                                  <MapPin className="w-4 h-4" />
                                  {bin.bin_code} (Cap: {bin.capacity})
                                </div>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label>Quantity *</Label>
                        <Input
                          type="number"
                          value={quantity}
                          onChange={(e) => setQuantity(parseInt(e.target.value) || 0)}
                          min={1}
                          max={selectedItem.quantity}
                          className="touch-input"
                          data-testid="putaway-quantity-input"
                        />
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex justify-end gap-3 pt-4">
                  <Button variant="outline" onClick={() => { setIsDialogOpen(false); resetForm(); }} className="touch-btn">
                    Cancel
                  </Button>
                  <Button
                    onClick={handleSubmit}
                    disabled={!selectedGRN || !selectedItem || !selectedBin || quantity < 1}
                    className="bg-[#f59e0b] hover:bg-[#d97706] touch-btn"
                    data-testid="putaway-submit-btn"
                  >
                    Create Putaway
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Putaway Cards */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="pt-6">
                <div className="h-32 bg-gray-200 rounded"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : putaways.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <ArrowDownToLine className="w-16 h-16 mx-auto mb-4 opacity-20" />
          <p className="text-lg">No putaway tasks found</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {putaways.map((putaway) => (
            <Card key={putaway.putaway_id} className="border border-gray-200 card-hover" data-testid={`putaway-card-${putaway.putaway_id}`}>
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-base font-mono">{putaway.material_code}</CardTitle>
                    <p className="text-sm text-gray-500 mt-1">From GRN: {putaway.grn_id.slice(0, 12)}...</p>
                  </div>
                  <Badge className={putaway.status === 'pending' ? 'badge-pending' : 'badge-completed'}>
                    {putaway.status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between text-sm">
                  <div className="flex items-center gap-2 text-gray-600">
                    <MapPin className="w-4 h-4" />
                    <span>To: {putaway.bin_code}</span>
                  </div>
                  <span className="font-bold tabular-nums text-lg">{putaway.quantity} units</span>
                </div>

                {putaway.status === 'pending' && canCreate && (
                  <Button
                    onClick={() => handleComplete(putaway)}
                    className="w-full bg-green-600 hover:bg-green-700 touch-btn"
                    data-testid={`complete-putaway-${putaway.putaway_id}`}
                  >
                    <Check className="w-5 h-5 mr-2" />
                    Complete Putaway
                  </Button>
                )}

                {putaway.completed_at && (
                  <p className="text-xs text-gray-500 text-center">
                    Completed: {new Date(putaway.completed_at).toLocaleString()}
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default Putaway;
