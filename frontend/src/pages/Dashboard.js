import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { dashboardAPI } from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import {
  Package,
  MapPin,
  FileInput,
  ArrowUpFromLine,
  ArrowDownToLine,
  AlertTriangle,
  TrendingUp,
  ArrowRight,
  Activity
} from 'lucide-react';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const response = await dashboardAPI.getStats();
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="pt-6">
                <div className="h-20 bg-gray-200 rounded"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  const statCards = [
    {
      title: 'Total Materials',
      value: stats?.total_materials || 0,
      icon: Package,
      color: 'bg-blue-500',
      link: '/materials'
    },
    {
      title: 'Total Stock',
      value: stats?.total_stock?.toLocaleString() || 0,
      icon: TrendingUp,
      color: 'bg-green-500',
      link: '/materials'
    },
    {
      title: 'Total Bins',
      value: stats?.total_bins || 0,
      icon: MapPin,
      color: 'bg-purple-500',
      link: '/bins'
    },
    {
      title: 'Low Stock Alerts',
      value: stats?.low_stock_count || 0,
      icon: AlertTriangle,
      color: 'bg-red-500',
      link: '/materials'
    }
  ];

  const pendingCards = [
    {
      title: 'Pending GRNs',
      value: stats?.pending_grns || 0,
      icon: FileInput,
      color: 'text-amber-600 bg-amber-50',
      link: '/grn'
    },
    {
      title: 'Pending Putaway',
      value: stats?.pending_putaways || 0,
      icon: ArrowDownToLine,
      color: 'text-blue-600 bg-blue-50',
      link: '/putaway'
    },
    {
      title: 'Pending Issues',
      value: stats?.pending_issues || 0,
      icon: ArrowUpFromLine,
      color: 'text-orange-600 bg-orange-50',
      link: '/issues'
    }
  ];

  const binStatusData = [
    { label: 'Available', value: stats?.available_bins || 0, className: 'badge-available' },
    { label: 'Empty', value: stats?.empty_bins || 0, className: 'badge-empty' },
    { label: 'Blocked', value: stats?.blocked_bins || 0, className: 'badge-blocked' }
  ];

  return (
    <div className="space-y-6">
      {/* Main Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6" data-testid="dashboard-stats-grid">
        {statCards.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <Link to={stat.link} key={index}>
              <Card className="card-hover cursor-pointer border border-gray-200">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500 font-medium">{stat.title}</p>
                      <p className="text-3xl font-bold text-gray-900 mt-1 tabular-nums">{stat.value}</p>
                    </div>
                    <div className={`${stat.color} p-3 rounded-xl`}>
                      <Icon className="w-6 h-6 text-white" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>

      {/* Pending Actions & Bin Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pending Actions */}
        <Card className="lg:col-span-2 border border-gray-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg font-semibold">Pending Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {pendingCards.map((card, index) => {
                const Icon = card.icon;
                return (
                  <Link to={card.link} key={index}>
                    <div className={`${card.color} p-4 rounded-xl card-hover cursor-pointer`}>
                      <div className="flex items-center justify-between mb-2">
                        <Icon className="w-5 h-5" />
                        <ArrowRight className="w-4 h-4 opacity-50" />
                      </div>
                      <p className="text-2xl font-bold tabular-nums">{card.value}</p>
                      <p className="text-sm opacity-80">{card.title}</p>
                    </div>
                  </Link>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Bin Status */}
        <Card className="border border-gray-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg font-semibold">Bin Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {binStatusData.map((item, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-600">{item.label}</span>
                  <Badge className={item.className}>{item.value}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Low Stock Materials & Recent Movements */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Low Stock Materials */}
        <Card className="border border-gray-200">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-semibold flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-red-500" />
                Low Stock Materials
              </CardTitle>
              <Link to="/materials" className="text-sm text-[#f59e0b] hover:text-[#d97706]">
                View All
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {stats?.low_stock_materials?.length > 0 ? (
              <div className="space-y-2">
                {stats.low_stock_materials.slice(0, 5).map((material, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-red-50 rounded-lg border border-red-100">
                    <div>
                      <p className="font-medium text-gray-900 font-mono text-sm">{material.material_code}</p>
                      <p className="text-sm text-gray-500">{material.name}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-red-600 font-bold tabular-nums">{material.current_stock}</p>
                      <p className="text-xs text-gray-500">Reorder: {material.reorder_point}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Package className="w-12 h-12 mx-auto mb-2 opacity-20" />
                <p>No low stock materials</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Movements */}
        <Card className="border border-gray-200">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-semibold flex items-center gap-2">
                <Activity className="w-5 h-5 text-blue-500" />
                Recent Movements
              </CardTitle>
              <Link to="/reports" className="text-sm text-[#f59e0b] hover:text-[#d97706]">
                View All
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {stats?.recent_movements?.length > 0 ? (
              <div className="space-y-2">
                {stats.recent_movements.slice(0, 5).map((movement, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      {movement.movement_type === 'inward' && <ArrowDownToLine className="w-4 h-4 text-green-500" />}
                      {movement.movement_type === 'outward' && <ArrowUpFromLine className="w-4 h-4 text-red-500" />}
                      {movement.movement_type === 'transfer' && <ArrowRight className="w-4 h-4 text-blue-500" />}
                      <div>
                        <p className="font-medium text-gray-900 font-mono text-sm">{movement.material_code}</p>
                        <p className="text-xs text-gray-500 capitalize">{movement.movement_type}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-bold tabular-nums text-gray-900">{movement.quantity}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(movement.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Activity className="w-12 h-12 mx-auto mb-2 opacity-20" />
                <p>No recent movements</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
