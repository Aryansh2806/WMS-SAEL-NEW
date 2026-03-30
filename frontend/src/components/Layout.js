import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  LayoutDashboard,
  Package,
  FileInput,
  Tags,
  MapPin,
  ArrowDownToLine,
  ArrowUpFromLine,
  BarChart3,
  Users,
  LogOut,
  Menu,
  X,
  ChevronDown,
  Settings,
  PieChart
} from 'lucide-react';
import { Button } from './ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator
} from './ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';

const navItems = [
  { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', roles: ['Admin', 'Warehouse Operator', 'Store In-Charge', 'Inventory Controller', 'Auditor', 'Management Viewer'] },
  { path: '/stock-dashboard', icon: PieChart, label: 'Stock Analytics', roles: ['Admin', 'Store In-Charge', 'Inventory Controller', 'Auditor', 'Management Viewer'] },
  { path: '/materials', icon: Package, label: 'Material Master', roles: ['Admin', 'Store In-Charge', 'Inventory Controller', 'Auditor'] },
  { path: '/grn', icon: FileInput, label: 'GRN / Inward', roles: ['Admin', 'Store In-Charge', 'Warehouse Operator', 'Inventory Controller', 'Auditor'] },
  { path: '/labels', icon: Tags, label: 'Labels', roles: ['Admin', 'Store In-Charge', 'Warehouse Operator'] },
  { path: '/bins', icon: MapPin, label: 'Bin Locations', roles: ['Admin', 'Store In-Charge', 'Inventory Controller', 'Auditor'] },
  { path: '/putaway', icon: ArrowDownToLine, label: 'Putaway', roles: ['Admin', 'Store In-Charge', 'Warehouse Operator'] },
  { path: '/issues', icon: ArrowUpFromLine, label: 'Material Issue', roles: ['Admin', 'Store In-Charge', 'Warehouse Operator'] },
  { path: '/reports', icon: BarChart3, label: 'Reports', roles: ['Admin', 'Store In-Charge', 'Inventory Controller', 'Auditor', 'Management Viewer'] },
  { path: '/users', icon: Users, label: 'User Management', roles: ['Admin'] },
];

export const Layout = ({ children }) => {
  const { user, logout, hasPermission } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const filteredNavItems = navItems.filter(item => hasPermission(item.roles));

  const getInitials = (name) => {
    if (!name) return 'U';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  return (
    <div className="min-h-screen flex bg-[#f9fafb]">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-[#1a2744] transform transition-transform duration-300 ease-in-out ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between h-16 px-4 border-b border-[#2d3c5f]">
            <Link to="/dashboard" className="flex items-center gap-2" data-testid="sidebar-logo">
              <Package className="w-8 h-8 text-[#f59e0b]" />
              <span className="text-white font-semibold text-lg">WMS Pro</span>
            </Link>
            <button
              className="lg:hidden text-white p-1"
              onClick={() => setSidebarOpen(false)}
              data-testid="sidebar-close-btn"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 py-4 px-3 overflow-y-auto">
            <ul className="space-y-1">
              {filteredNavItems.map((item) => {
                const isActive = location.pathname === item.path || location.pathname.startsWith(item.path + '/');
                const Icon = item.icon;
                
                return (
                  <li key={item.path}>
                    <Link
                      to={item.path}
                      onClick={() => setSidebarOpen(false)}
                      data-testid={`sidebar-${item.label.toLowerCase().replace(/\s+/g, '-')}-link`}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
                        isActive
                          ? 'bg-[#2e416b] text-white'
                          : 'text-[#9ca3af] hover:bg-[#263659] hover:text-white'
                      }`}
                    >
                      <Icon className="w-5 h-5 flex-shrink-0" />
                      <span className="text-sm font-medium">{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>

          {/* User section */}
          <div className="p-4 border-t border-[#2d3c5f]">
            <div className="flex items-center gap-3">
              <Avatar className="w-10 h-10">
                <AvatarImage src={user?.picture} />
                <AvatarFallback className="bg-[#f59e0b] text-white text-sm">
                  {getInitials(user?.name)}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="text-white text-sm font-medium truncate">{user?.name}</p>
                <p className="text-[#9ca3af] text-xs truncate">{user?.role}</p>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-h-screen lg:ml-0">
        {/* Header */}
        <header className="sticky top-0 z-40 h-16 bg-white border-b border-gray-200 px-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              className="lg:hidden p-2 rounded-lg hover:bg-gray-100"
              onClick={() => setSidebarOpen(true)}
              data-testid="sidebar-toggle-btn"
            >
              <Menu className="w-6 h-6 text-gray-600" />
            </button>
            <h1 className="text-lg font-semibold text-gray-900">
              {filteredNavItems.find(item => location.pathname.startsWith(item.path))?.label || 'Dashboard'}
            </h1>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="flex items-center gap-2" data-testid="user-menu-btn">
                <Avatar className="w-8 h-8">
                  <AvatarImage src={user?.picture} />
                  <AvatarFallback className="bg-[#f59e0b] text-white text-xs">
                    {getInitials(user?.name)}
                  </AvatarFallback>
                </Avatar>
                <span className="hidden sm:inline text-sm font-medium">{user?.name}</span>
                <ChevronDown className="w-4 h-4 text-gray-500" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <div className="px-2 py-1.5">
                <p className="text-sm font-medium">{user?.name}</p>
                <p className="text-xs text-gray-500">{user?.email}</p>
              </div>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-xs text-gray-500">
                <Settings className="w-4 h-4 mr-2" />
                Role: {user?.role}
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={handleLogout}
                className="text-red-600 focus:text-red-600"
                data-testid="logout-btn"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </header>

        {/* Page content */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;
