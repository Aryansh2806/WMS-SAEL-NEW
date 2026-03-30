import React, { useState, useEffect } from 'react';
import { materialAPI } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Plus, Search, Edit, Trash2, Package, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';

const CATEGORIES = ['Raw Materials', 'Packaging', 'Spares', 'Finished Goods', 'Consumables', 'Equipment'];
const UOMS = ['PCS', 'KG', 'LTR', 'MTR', 'BOX', 'SET', 'ROLL'];

const Materials = () => {
  const { hasPermission } = useAuth();
  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingMaterial, setEditingMaterial] = useState(null);
  const [formData, setFormData] = useState({
    material_code: '',
    name: '',
    description: '',
    category: 'Raw Materials',
    uom: 'PCS',
    stock_method: 'FIFO',
    min_stock_level: 10,
    max_stock_level: 1000,
    reorder_point: 50
  });

  // Only Admin can create/edit/delete master data
  const canCreate = hasPermission(['Admin']);
  const canEdit = hasPermission(['Admin']);
  const canDelete = hasPermission(['Admin']);

  useEffect(() => {
    loadMaterials();
  }, [categoryFilter, searchTerm]);

  const loadMaterials = async () => {
    try {
      const params = {};
      if (categoryFilter && categoryFilter !== 'all') params.category = categoryFilter;
      if (searchTerm) params.search = searchTerm;
      
      const response = await materialAPI.getAll(params);
      setMaterials(response.data);
    } catch (error) {
      toast.error('Failed to load materials');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingMaterial) {
        await materialAPI.update(editingMaterial.material_id, formData);
        toast.success('Material updated successfully');
      } else {
        await materialAPI.create(formData);
        toast.success('Material created successfully');
      }
      setIsDialogOpen(false);
      resetForm();
      loadMaterials();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    }
  };

  const handleEdit = (material) => {
    setEditingMaterial(material);
    setFormData({
      material_code: material.material_code,
      name: material.name,
      description: material.description || '',
      category: material.category,
      uom: material.uom,
      stock_method: material.stock_method,
      min_stock_level: material.min_stock_level,
      max_stock_level: material.max_stock_level,
      reorder_point: material.reorder_point
    });
    setIsDialogOpen(true);
  };

  const handleDelete = async (material) => {
    if (!window.confirm(`Delete ${material.material_code}?`)) return;
    
    try {
      await materialAPI.delete(material.material_id);
      toast.success('Material deleted successfully');
      loadMaterials();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Delete failed');
    }
  };

  const resetForm = () => {
    setEditingMaterial(null);
    setFormData({
      material_code: '',
      name: '',
      description: '',
      category: 'Raw Materials',
      uom: 'PCS',
      stock_method: 'FIFO',
      min_stock_level: 10,
      max_stock_level: 1000,
      reorder_point: 50
    });
  };

  const getStockStatus = (material) => {
    if (material.current_stock <= 0) return { label: 'Out of Stock', className: 'badge-blocked' };
    if (material.current_stock <= material.reorder_point) return { label: 'Low Stock', className: 'badge-hold' };
    return { label: 'In Stock', className: 'badge-available' };
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between">
        <div className="flex flex-1 gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Search materials..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
              data-testid="material-search-input"
            />
          </div>
          <Select value={categoryFilter} onValueChange={setCategoryFilter}>
            <SelectTrigger className="w-48" data-testid="category-filter-select">
              <SelectValue placeholder="All Categories" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Categories</SelectItem>
              {CATEGORIES.map((cat) => (
                <SelectItem key={cat} value={cat}>{cat}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {canCreate && (
          <Dialog open={isDialogOpen} onOpenChange={(open) => { setIsDialogOpen(open); if (!open) resetForm(); }}>
            <DialogTrigger asChild>
              <Button className="bg-[#f59e0b] hover:bg-[#d97706]" data-testid="add-material-btn">
                <Plus className="w-4 h-4 mr-2" />
                Add Material
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>{editingMaterial ? 'Edit Material' : 'Add New Material'}</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Material Code *</Label>
                    <Input
                      value={formData.material_code}
                      onChange={(e) => setFormData({ ...formData, material_code: e.target.value.toUpperCase() })}
                      placeholder="e.g., RAW-001"
                      required
                      disabled={!!editingMaterial}
                      data-testid="material-code-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Name *</Label>
                    <Input
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="Material name"
                      required
                      data-testid="material-name-input"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Description</Label>
                  <Input
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Optional description"
                    data-testid="material-description-input"
                  />
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Category *</Label>
                    <Select value={formData.category} onValueChange={(v) => setFormData({ ...formData, category: v })}>
                      <SelectTrigger data-testid="material-category-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {CATEGORIES.map((cat) => (
                          <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>UOM *</Label>
                    <Select value={formData.uom} onValueChange={(v) => setFormData({ ...formData, uom: v })}>
                      <SelectTrigger data-testid="material-uom-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {UOMS.map((uom) => (
                          <SelectItem key={uom} value={uom}>{uom}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Stock Method *</Label>
                    <Select value={formData.stock_method} onValueChange={(v) => setFormData({ ...formData, stock_method: v })}>
                      <SelectTrigger data-testid="material-stock-method-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="FIFO">FIFO</SelectItem>
                        <SelectItem value="LIFO">LIFO</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Min Stock Level</Label>
                    <Input
                      type="number"
                      value={formData.min_stock_level}
                      onChange={(e) => setFormData({ ...formData, min_stock_level: parseInt(e.target.value) || 0 })}
                      min={0}
                      data-testid="material-min-stock-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Max Stock Level</Label>
                    <Input
                      type="number"
                      value={formData.max_stock_level}
                      onChange={(e) => setFormData({ ...formData, max_stock_level: parseInt(e.target.value) || 0 })}
                      min={0}
                      data-testid="material-max-stock-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Reorder Point</Label>
                    <Input
                      type="number"
                      value={formData.reorder_point}
                      onChange={(e) => setFormData({ ...formData, reorder_point: parseInt(e.target.value) || 0 })}
                      min={0}
                      data-testid="material-reorder-point-input"
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <Button type="button" variant="outline" onClick={() => { setIsDialogOpen(false); resetForm(); }}>
                    Cancel
                  </Button>
                  <Button type="submit" className="bg-[#f59e0b] hover:bg-[#d97706]" data-testid="material-submit-btn">
                    {editingMaterial ? 'Update' : 'Create'} Material
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Materials Table */}
      <Card className="border border-gray-200">
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-gray-500">Loading materials...</div>
          ) : materials.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <Package className="w-12 h-12 mx-auto mb-2 opacity-20" />
              <p>No materials found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-gray-50">
                    <TableHead className="font-semibold">Code</TableHead>
                    <TableHead className="font-semibold">Name</TableHead>
                    <TableHead className="font-semibold">Category</TableHead>
                    <TableHead className="font-semibold">UOM</TableHead>
                    <TableHead className="font-semibold">Stock Method</TableHead>
                    <TableHead className="font-semibold text-right">Current Stock</TableHead>
                    <TableHead className="font-semibold">Status</TableHead>
                    {canEdit && <TableHead className="font-semibold text-right">Actions</TableHead>}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {materials.map((material) => {
                    const stockStatus = getStockStatus(material);
                    const isLowStock = material.current_stock <= material.reorder_point;
                    
                    return (
                      <TableRow key={material.material_id} className="hover:bg-gray-50" data-testid={`material-row-${material.material_code}`}>
                        <TableCell className="font-mono font-medium">{material.material_code}</TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{material.name}</p>
                            {material.description && (
                              <p className="text-xs text-gray-500 truncate max-w-xs">{material.description}</p>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>{material.category}</TableCell>
                        <TableCell>{material.uom}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{material.stock_method}</Badge>
                        </TableCell>
                        <TableCell className="text-right tabular-nums">
                          <div className="flex items-center justify-end gap-2">
                            {isLowStock && <AlertTriangle className="w-4 h-4 text-amber-500" />}
                            <span className={isLowStock ? 'text-amber-600 font-medium' : ''}>
                              {material.current_stock}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={stockStatus.className}>{stockStatus.label}</Badge>
                        </TableCell>
                        {canEdit && (
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-2">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleEdit(material)}
                                data-testid={`edit-material-${material.material_code}`}
                              >
                                <Edit className="w-4 h-4" />
                              </Button>
                              {canDelete && material.current_stock === 0 && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="text-red-600 hover:text-red-700"
                                  onClick={() => handleDelete(material)}
                                  data-testid={`delete-material-${material.material_code}`}
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              )}
                            </div>
                          </TableCell>
                        )}
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Materials;
