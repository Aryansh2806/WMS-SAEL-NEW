import React, { useState, useEffect } from 'react';
import { binAPI } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Plus, MapPin, Edit } from 'lucide-react';
import { toast } from 'sonner';

const BIN_TYPES = ['storage', 'picking', 'staging', 'quarantine'];
const BIN_STATUSES = ['empty', 'available', 'blocked', 'quality_hold'];

const Bins = () => {
  const { hasPermission } = useAuth();
  const [bins, setBins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [zoneFilter, setZoneFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [zones, setZones] = useState([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingBin, setEditingBin] = useState(null);
  const [formData, setFormData] = useState({
    bin_code: '',
    zone: '',
    aisle: '',
    rack: '',
    level: '',
    capacity: 100,
    bin_type: 'storage'
  });

  // Only Admin can create/edit bins (master data)
  const canCreate = hasPermission(['Admin']);
  const canEdit = hasPermission(['Admin']);
  const canChangeStatus = hasPermission(['Admin', 'Store In-Charge']);

  useEffect(() => {
    loadData();
  }, [zoneFilter, statusFilter]);

  const loadData = async () => {
    try {
      const params = {};
      if (zoneFilter && zoneFilter !== 'all') params.zone = zoneFilter;
      if (statusFilter && statusFilter !== 'all') params.status = statusFilter;
      
      const [binsRes, zonesRes] = await Promise.all([
        binAPI.getAll(params),
        binAPI.getZones()
      ]);
      setBins(binsRes.data);
      setZones(zonesRes.data);
    } catch (error) {
      toast.error('Failed to load bins');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingBin) {
        await binAPI.update(editingBin.bin_id, formData);
        toast.success('Bin updated successfully');
      } else {
        await binAPI.create(formData);
        toast.success('Bin created successfully');
      }
      setIsDialogOpen(false);
      resetForm();
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    }
  };

  const handleEdit = (bin) => {
    setEditingBin(bin);
    setFormData({
      bin_code: bin.bin_code,
      zone: bin.zone,
      aisle: bin.aisle,
      rack: bin.rack,
      level: bin.level,
      capacity: bin.capacity,
      bin_type: bin.bin_type
    });
    setIsDialogOpen(true);
  };

  const handleStatusChange = async (bin, newStatus) => {
    try {
      await binAPI.updateStatus(bin.bin_id, newStatus);
      toast.success('Bin status updated');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Status update failed');
    }
  };

  const resetForm = () => {
    setEditingBin(null);
    setFormData({
      bin_code: '',
      zone: '',
      aisle: '',
      rack: '',
      level: '',
      capacity: 100,
      bin_type: 'storage'
    });
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'available': return <Badge className="badge-available">Available</Badge>;
      case 'blocked': return <Badge className="badge-blocked">Blocked</Badge>;
      case 'quality_hold': return <Badge className="badge-hold">Quality Hold</Badge>;
      case 'empty': return <Badge className="badge-empty">Empty</Badge>;
      default: return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getUtilization = (bin) => {
    const percent = Math.round((bin.current_stock / bin.capacity) * 100);
    let color = 'bg-green-500';
    if (percent > 90) color = 'bg-red-500';
    else if (percent > 70) color = 'bg-amber-500';
    
    return (
      <div className="flex items-center gap-2">
        <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div className={`h-full ${color} transition-all`} style={{ width: `${percent}%` }} />
        </div>
        <span className="text-xs tabular-nums">{percent}%</span>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between">
        <div className="flex gap-4">
          <Select value={zoneFilter} onValueChange={setZoneFilter}>
            <SelectTrigger className="w-40" data-testid="zone-filter-select">
              <SelectValue placeholder="All Zones" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Zones</SelectItem>
              {zones.map((zone) => (
                <SelectItem key={zone} value={zone}>Zone {zone}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-40" data-testid="status-filter-select">
              <SelectValue placeholder="All Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              {BIN_STATUSES.map((status) => (
                <SelectItem key={status} value={status} className="capitalize">{status.replace('_', ' ')}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {canCreate && (
          <Dialog open={isDialogOpen} onOpenChange={(open) => { setIsDialogOpen(open); if (!open) resetForm(); }}>
            <DialogTrigger asChild>
              <Button className="bg-[#f59e0b] hover:bg-[#d97706]" data-testid="add-bin-btn">
                <Plus className="w-4 h-4 mr-2" />
                Add Bin
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>{editingBin ? 'Edit Bin' : 'Add New Bin'}</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label>Bin Code *</Label>
                  <Input
                    value={formData.bin_code}
                    onChange={(e) => setFormData({ ...formData, bin_code: e.target.value.toUpperCase() })}
                    placeholder="e.g., A-01-02-03"
                    required
                    disabled={!!editingBin}
                    data-testid="bin-code-input"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Zone *</Label>
                    <Input
                      value={formData.zone}
                      onChange={(e) => setFormData({ ...formData, zone: e.target.value.toUpperCase() })}
                      placeholder="e.g., A"
                      required
                      data-testid="bin-zone-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Aisle *</Label>
                    <Input
                      value={formData.aisle}
                      onChange={(e) => setFormData({ ...formData, aisle: e.target.value })}
                      placeholder="e.g., 01"
                      required
                      data-testid="bin-aisle-input"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Rack *</Label>
                    <Input
                      value={formData.rack}
                      onChange={(e) => setFormData({ ...formData, rack: e.target.value })}
                      placeholder="e.g., 02"
                      required
                      data-testid="bin-rack-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Level *</Label>
                    <Input
                      value={formData.level}
                      onChange={(e) => setFormData({ ...formData, level: e.target.value })}
                      placeholder="e.g., 03"
                      required
                      data-testid="bin-level-input"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Capacity *</Label>
                    <Input
                      type="number"
                      value={formData.capacity}
                      onChange={(e) => setFormData({ ...formData, capacity: parseInt(e.target.value) || 0 })}
                      min={1}
                      required
                      data-testid="bin-capacity-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Bin Type *</Label>
                    <Select value={formData.bin_type} onValueChange={(v) => setFormData({ ...formData, bin_type: v })}>
                      <SelectTrigger data-testid="bin-type-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {BIN_TYPES.map((type) => (
                          <SelectItem key={type} value={type} className="capitalize">{type}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <Button type="button" variant="outline" onClick={() => { setIsDialogOpen(false); resetForm(); }}>
                    Cancel
                  </Button>
                  <Button type="submit" className="bg-[#f59e0b] hover:bg-[#d97706]" data-testid="bin-submit-btn">
                    {editingBin ? 'Update' : 'Create'} Bin
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Bins Table */}
      <Card className="border border-gray-200">
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-gray-500">Loading bins...</div>
          ) : bins.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <MapPin className="w-12 h-12 mx-auto mb-2 opacity-20" />
              <p>No bins found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-gray-50">
                    <TableHead className="font-semibold">Bin Code</TableHead>
                    <TableHead className="font-semibold">Zone</TableHead>
                    <TableHead className="font-semibold">Location</TableHead>
                    <TableHead className="font-semibold">Type</TableHead>
                    <TableHead className="font-semibold">Material</TableHead>
                    <TableHead className="font-semibold">Utilization</TableHead>
                    <TableHead className="font-semibold">Status</TableHead>
                    {(canEdit || canChangeStatus) && <TableHead className="font-semibold text-right">Actions</TableHead>}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {bins.map((bin) => (
                    <TableRow key={bin.bin_id} className="hover:bg-gray-50" data-testid={`bin-row-${bin.bin_code}`}>
                      <TableCell className="font-mono font-medium">{bin.bin_code}</TableCell>
                      <TableCell>Zone {bin.zone}</TableCell>
                      <TableCell className="text-sm text-gray-600">
                        Aisle {bin.aisle}, Rack {bin.rack}, Level {bin.level}
                      </TableCell>
                      <TableCell className="capitalize">{bin.bin_type}</TableCell>
                      <TableCell>
                        {bin.material_code ? (
                          <span className="font-mono text-sm">{bin.material_code}</span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </TableCell>
                      <TableCell>{getUtilization(bin)}</TableCell>
                      <TableCell>
                        {canChangeStatus ? (
                          <Select value={bin.status} onValueChange={(v) => handleStatusChange(bin, v)}>
                            <SelectTrigger className="w-32 h-8" data-testid={`bin-status-${bin.bin_code}`}>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {BIN_STATUSES.map((status) => (
                                <SelectItem key={status} value={status} className="capitalize">
                                  {status.replace('_', ' ')}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        ) : (
                          getStatusBadge(bin.status)
                        )}
                      </TableCell>
                      {(canEdit || canChangeStatus) && (
                        <TableCell className="text-right">
                          {canEdit && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleEdit(bin)}
                              data-testid={`edit-bin-${bin.bin_code}`}
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                          )}
                        </TableCell>
                      )}
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

export default Bins;
