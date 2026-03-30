import React, { useState, useEffect, useCallback } from 'react';
import { dashboardAPI } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  Package, MapPin, AlertTriangle, TrendingUp, TrendingDown, 
  Clock, RefreshCw, Layers, BarChart3, PieChart, Activity,
  AlertCircle, CheckCircle, XCircle, Timer, Warehouse, ArrowUp, ArrowDown
} from 'lucide-react';
import { toast } from 'sonner';
import {
  PieChart as RechartsPie, Pie, Cell, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend
} from 'recharts';

const COLORS = ['#22c55e', '#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6', '#ec4899'];
const STATUS_COLORS = {
  available: '#22c55e',
  blocked: '#ef4444',
  quality_hold: '#f59e0b'
};

const StockDashboard = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [summary, setSummary] = useState(null);
  const [aging, setAging] = useState(null);
  const [slowMoving, setSlowMoving] = useState(null);
  const [binUtil, setBinUtil] = useState(null);
  const [fifoAlerts, setFifoAlerts] = useState(null);
  const [materialStock, setMaterialStock] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const loadDashboard = useCallback(async (showRefresh = false) => {
    if (showRefresh) setRefreshing(true);
    else setLoading(true);
    
    try {
      const [summaryRes, agingRes, slowRes, binRes, fifoRes, matRes] = await Promise.all([
        dashboardAPI.stockSummary(),
        dashboardAPI.stockAging(),
        dashboardAPI.slowMoving(),
        dashboardAPI.binUtilization(),
        dashboardAPI.fifoAlerts(),
        dashboardAPI.materialStock()
      ]);
      
      setSummary(summaryRes.data);
      setAging(agingRes.data);
      setSlowMoving(slowRes.data);
      setBinUtil(binRes.data);
      setFifoAlerts(fifoRes.data);
      setMaterialStock(matRes.data);
      setLastUpdated(new Date());
      
      if (showRefresh) toast.success('Dashboard refreshed');
    } catch (error) {
      console.error('Dashboard load error:', error);
      toast.error('Failed to load dashboard');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => loadDashboard(false), 30000);
    return () => clearInterval(interval);
  }, [loadDashboard]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 animate-spin mx-auto text-[#f59e0b] mb-4" />
          <p className="text-gray-500">Loading Stock Dashboard...</p>
        </div>
      </div>
    );
  }

  // Prepare chart data
  const stockStatusData = summary ? [
    { name: 'Available', value: summary.stock_status?.available || 0, color: STATUS_COLORS.available },
    { name: 'Blocked', value: summary.stock_status?.blocked || 0, color: STATUS_COLORS.blocked },
    { name: 'Quality Hold', value: summary.stock_status?.quality_hold || 0, color: STATUS_COLORS.quality_hold }
  ].filter(d => d.value > 0) : [];

  const binStatusData = summary ? [
    { name: 'Occupied', value: summary.bin_summary?.occupied || 0 },
    { name: 'Empty', value: summary.bin_summary?.empty || 0 }
  ] : [];

  const agingChartData = aging ? [
    { name: '0-30 days', qty: aging.aging_buckets?.["0-30"]?.quantity || 0, count: aging.aging_buckets?.["0-30"]?.count || 0 },
    { name: '31-60 days', qty: aging.aging_buckets?.["31-60"]?.quantity || 0, count: aging.aging_buckets?.["31-60"]?.count || 0 },
    { name: '61-90 days', qty: aging.aging_buckets?.["61-90"]?.quantity || 0, count: aging.aging_buckets?.["61-90"]?.count || 0 },
    { name: '90+ days', qty: aging.aging_buckets?.["90+"]?.quantity || 0, count: aging.aging_buckets?.["90+"]?.count || 0 }
  ] : [];

  const categoryData = summary?.stock_by_category?.slice(0, 6).map((c, i) => ({
    name: c._id || 'Other',
    value: c.total_stock,
    color: COLORS[i % COLORS.length]
  })) || [];

  return (
    <div className="space-y-6" data-testid="stock-dashboard">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <BarChart3 className="w-7 h-7 text-[#f59e0b]" />
            Stock Dashboard
          </h1>
          <p className="text-gray-500">Real-time inventory visibility and analytics</p>
        </div>
        <div className="flex items-center gap-3">
          {lastUpdated && (
            <span className="text-sm text-gray-500">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </span>
          )}
          <Button 
            variant="outline" 
            onClick={() => loadDashboard(true)}
            disabled={refreshing}
            data-testid="refresh-dashboard"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Summary Cards Row 1 */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wide">Total Stock</p>
                <p className="text-2xl font-bold tabular-nums">{summary?.total_stock?.toLocaleString() || 0}</p>
              </div>
              <Package className="w-8 h-8 text-blue-500 opacity-80" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-green-500">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wide">Available</p>
                <p className="text-2xl font-bold tabular-nums text-green-600">
                  {summary?.stock_status?.available?.toLocaleString() || 0}
                </p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-500 opacity-80" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-red-500">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wide">Blocked</p>
                <p className="text-2xl font-bold tabular-nums text-red-600">
                  {summary?.stock_status?.blocked?.toLocaleString() || 0}
                </p>
              </div>
              <XCircle className="w-8 h-8 text-red-500 opacity-80" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-amber-500">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wide">Quality Hold</p>
                <p className="text-2xl font-bold tabular-nums text-amber-600">
                  {summary?.stock_status?.quality_hold?.toLocaleString() || 0}
                </p>
              </div>
              <AlertCircle className="w-8 h-8 text-amber-500 opacity-80" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wide">Overstock</p>
                <p className="text-2xl font-bold tabular-nums text-purple-600">
                  {summary?.overstock_count || 0}
                </p>
              </div>
              <ArrowUp className="w-8 h-8 text-purple-500 opacity-80" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-orange-500">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wide">Understock</p>
                <p className="text-2xl font-bold tabular-nums text-orange-600">
                  {summary?.understock_count || 0}
                </p>
              </div>
              <ArrowDown className="w-8 h-8 text-orange-500 opacity-80" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Stock Status Pie Chart */}
        <Card className="border border-gray-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <PieChart className="w-4 h-4" />
              Stock by Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-48">
              {stockStatusData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsPie>
                    <Pie
                      data={stockStatusData}
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={70}
                      paddingAngle={2}
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      labelLine={false}
                    >
                      {stockStatusData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </RechartsPie>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400">
                  No stock data
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Bin Status */}
        <Card className="border border-gray-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <Warehouse className="w-4 h-4" />
              Bin Utilization
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="text-center">
                <p className="text-4xl font-bold text-[#f59e0b]">{binUtil?.overall_utilization || 0}%</p>
                <p className="text-sm text-gray-500">Overall Utilization</p>
              </div>
              <div className="grid grid-cols-2 gap-4 text-center">
                <div className="p-3 bg-green-50 rounded-lg">
                  <p className="text-2xl font-bold text-green-600">{summary?.bin_summary?.occupied || 0}</p>
                  <p className="text-xs text-gray-500">Occupied</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-gray-600">{summary?.bin_summary?.empty || 0}</p>
                  <p className="text-xs text-gray-500">Empty</p>
                </div>
              </div>
              <Progress value={binUtil?.overall_utilization || 0} className="h-2" />
            </div>
          </CardContent>
        </Card>

        {/* Stock by Category */}
        <Card className="border border-gray-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <Layers className="w-4 h-4" />
              Stock by Category
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-48">
              {categoryData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsPie>
                    <Pie
                      data={categoryData}
                      cx="50%"
                      cy="50%"
                      outerRadius={70}
                      dataKey="value"
                      label={({ name }) => name.slice(0, 10)}
                      labelLine={false}
                    >
                      {categoryData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </RechartsPie>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400">
                  No category data
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Stock Aging Chart */}
      <Card className="border border-gray-200">
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center gap-2">
            <Clock className="w-4 h-4" />
            Stock Aging Analysis
          </CardTitle>
          <CardDescription>Stock quantity by age bucket</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={agingChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="qty" name="Quantity" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                <Bar dataKey="count" name="Batches" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Tabs */}
      <Tabs defaultValue="alerts" className="space-y-4">
        <TabsList>
          <TabsTrigger value="alerts" data-testid="alerts-tab">
            <AlertTriangle className="w-4 h-4 mr-2" />
            Alerts
          </TabsTrigger>
          <TabsTrigger value="bins" data-testid="bins-tab">
            <MapPin className="w-4 h-4 mr-2" />
            Bin Zones
          </TabsTrigger>
          <TabsTrigger value="materials" data-testid="materials-tab">
            <Package className="w-4 h-4 mr-2" />
            Top Materials
          </TabsTrigger>
          <TabsTrigger value="fifo" data-testid="fifo-tab">
            <Timer className="w-4 h-4 mr-2" />
            FIFO Status
          </TabsTrigger>
        </TabsList>

        {/* Alerts Tab */}
        <TabsContent value="alerts">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Understock Alerts */}
            <Card className="border border-red-200 bg-red-50/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2 text-red-700">
                  <TrendingDown className="w-4 h-4" />
                  Understock Items ({summary?.understock_count || 0})
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                {summary?.understock_items?.length > 0 ? (
                  <div className="divide-y divide-red-100">
                    {summary.understock_items.map((item, idx) => (
                      <div key={idx} className="px-4 py-3 flex justify-between items-center">
                        <div>
                          <p className="font-mono font-medium text-sm">{item.material_code}</p>
                          <p className="text-xs text-gray-500">{item.name?.slice(0, 25)}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-red-600">{item.current_stock}</p>
                          <p className="text-xs text-gray-500">Min: {item.min_level}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="p-4 text-center text-gray-500 text-sm">No understock alerts</p>
                )}
              </CardContent>
            </Card>

            {/* Overstock Alerts */}
            <Card className="border border-purple-200 bg-purple-50/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2 text-purple-700">
                  <TrendingUp className="w-4 h-4" />
                  Overstock Items ({summary?.overstock_count || 0})
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                {summary?.overstock_items?.length > 0 ? (
                  <div className="divide-y divide-purple-100">
                    {summary.overstock_items.map((item, idx) => (
                      <div key={idx} className="px-4 py-3 flex justify-between items-center">
                        <div>
                          <p className="font-mono font-medium text-sm">{item.material_code}</p>
                          <p className="text-xs text-gray-500">{item.name?.slice(0, 25)}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-purple-600">{item.current_stock}</p>
                          <p className="text-xs text-gray-500">Max: {item.max_level}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="p-4 text-center text-gray-500 text-sm">No overstock alerts</p>
                )}
              </CardContent>
            </Card>

            {/* Slow/Non-Moving Stock */}
            <Card className="border border-amber-200 bg-amber-50/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2 text-amber-700">
                  <Clock className="w-4 h-4" />
                  Slow/Non-Moving ({(slowMoving?.slow_moving_count || 0) + (slowMoving?.non_moving_count || 0)})
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                {(slowMoving?.slow_moving_items?.length > 0 || slowMoving?.non_moving_items?.length > 0) ? (
                  <div className="divide-y divide-amber-100">
                    {[...(slowMoving?.non_moving_items || []), ...(slowMoving?.slow_moving_items || [])].slice(0, 5).map((item, idx) => (
                      <div key={idx} className="px-4 py-3 flex justify-between items-center">
                        <div>
                          <p className="font-mono font-medium text-sm">{item.material_code}</p>
                          <p className="text-xs text-gray-500">{item.name?.slice(0, 25)}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-amber-600">{item.current_stock}</p>
                          <p className="text-xs text-gray-500">{item.days_idle} days idle</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="p-4 text-center text-gray-500 text-sm">No slow-moving stock</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Bins Tab */}
        <TabsContent value="bins">
          <Card className="border border-gray-200">
            <CardHeader>
              <CardTitle className="text-base">Zone-wise Bin Utilization</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Zone</TableHead>
                    <TableHead className="text-right">Total Bins</TableHead>
                    <TableHead className="text-right">Occupied</TableHead>
                    <TableHead className="text-right">Empty</TableHead>
                    <TableHead className="text-right">Capacity</TableHead>
                    <TableHead className="text-right">Used</TableHead>
                    <TableHead>Utilization</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {binUtil?.zone_summary?.map((zone, idx) => (
                    <TableRow key={idx}>
                      <TableCell className="font-medium">Zone {zone.zone}</TableCell>
                      <TableCell className="text-right">{zone.total}</TableCell>
                      <TableCell className="text-right text-green-600">{zone.occupied}</TableCell>
                      <TableCell className="text-right text-gray-500">{zone.empty}</TableCell>
                      <TableCell className="text-right">{zone.total_capacity?.toLocaleString()}</TableCell>
                      <TableCell className="text-right">{zone.used_capacity?.toLocaleString()}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Progress value={zone.utilization_percent} className="h-2 w-20" />
                          <span className="text-sm font-medium">{zone.utilization_percent}%</span>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Materials Tab */}
        <TabsContent value="materials">
          <Card className="border border-gray-200">
            <CardHeader>
              <CardTitle className="text-base">Top 10 Materials by Stock</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Material Code</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead className="text-right">Stock</TableHead>
                    <TableHead>UOM</TableHead>
                    <TableHead>Method</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {materialStock?.top_stock_materials?.map((mat, idx) => (
                    <TableRow key={idx}>
                      <TableCell className="font-mono font-medium">{mat.material_code}</TableCell>
                      <TableCell>{mat.name?.slice(0, 30)}</TableCell>
                      <TableCell>{mat.category}</TableCell>
                      <TableCell className="text-right font-bold tabular-nums">{mat.current_stock?.toLocaleString()}</TableCell>
                      <TableCell>{mat.uom}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{mat.stock_method}</Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* FIFO Tab */}
        <TabsContent value="fifo">
          <Card className="border border-gray-200">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Timer className="w-4 h-4" />
                FIFO Materials Pending Stock ({fifoAlerts?.fifo_materials_count || 0})
              </CardTitle>
              <CardDescription>Materials configured for FIFO with oldest batch information</CardDescription>
            </CardHeader>
            <CardContent>
              {fifoAlerts?.alerts?.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Material Code</TableHead>
                      <TableHead>Name</TableHead>
                      <TableHead className="text-right">Current Stock</TableHead>
                      <TableHead>Oldest Batch</TableHead>
                      <TableHead>Receipt Date</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {fifoAlerts.alerts.map((alert, idx) => (
                      <TableRow key={idx}>
                        <TableCell className="font-mono font-medium">{alert.material_code}</TableCell>
                        <TableCell>{alert.name?.slice(0, 30)}</TableCell>
                        <TableCell className="text-right font-bold">{alert.current_stock}</TableCell>
                        <TableCell className="font-mono text-sm">{alert.oldest_batch}</TableCell>
                        <TableCell>{alert.receipt_date?.slice(0, 10)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <p className="text-center text-gray-500 py-8">No FIFO materials with pending stock</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Expiring Soon Alert */}
      {aging?.expiring_soon?.length > 0 && (
        <Card className="border-2 border-red-300 bg-red-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2 text-red-700">
              <AlertTriangle className="w-5 h-5" />
              Expiring Soon ({aging.expiring_soon.length} items)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {aging.expiring_soon.slice(0, 8).map((item, idx) => (
                <div key={idx} className="bg-white rounded-lg p-3 border border-red-200">
                  <p className="font-mono font-medium text-sm">{item.material_code}</p>
                  <p className="text-xs text-gray-500">Batch: {item.batch_number}</p>
                  <div className="flex justify-between items-center mt-2">
                    <span className="text-sm">Qty: {item.quantity}</span>
                    <Badge className="bg-red-100 text-red-700">{item.days_to_expiry} days</Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default StockDashboard;
