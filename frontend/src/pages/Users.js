import React, { useState, useEffect } from 'react';
import { userAPI, auditAPI } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Users, UserCheck, UserX, Shield, Plus, History, Search, Trash2, Edit, Eye, FileText } from 'lucide-react';
import { toast } from 'sonner';

const ROLES = [
  'Admin',
  'Warehouse Operator',
  'Store In-Charge',
  'Inventory Controller',
  'Auditor',
  'Management Viewer'
];

const ROLE_DESCRIPTIONS = {
  'Admin': 'Full access to all modules including master data management',
  'Warehouse Operator': 'GRN, putaway, and material issue operations',
  'Store In-Charge': 'All operations plus approvals (no master data changes)',
  'Inventory Controller': 'Stock inquiry and reports (read-only)',
  'Auditor': 'Read-only access to all data including audit trail',
  'Management Viewer': 'Dashboard view only'
};

const UserManagement = () => {
  const { user: currentUser, hasPermission } = useAuth();
  const [users, setUsers] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [auditSummary, setAuditSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('users');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isViewDialogOpen, setIsViewDialogOpen] = useState(false);
  const [viewingUser, setViewingUser] = useState(null);
  const [userAuditHistory, setUserAuditHistory] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Form state
  const [formData, setFormData] = useState({
    email: '',
    name: '',
    password: '',
    role: 'Warehouse Operator'
  });

  const isAdmin = hasPermission(['Admin']);
  const canViewAudit = hasPermission(['Admin', 'Auditor', 'Store In-Charge', 'Inventory Controller']);

  useEffect(() => {
    loadUsers();
    if (canViewAudit) {
      loadAuditData();
    }
  }, [canViewAudit]);

  const loadUsers = async () => {
    try {
      const response = await userAPI.getAll();
      setUsers(response.data);
    } catch (error) {
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const loadAuditData = async () => {
    try {
      const [logsRes, summaryRes] = await Promise.all([
        auditAPI.getAll({ limit: 50 }),
        auditAPI.getSummary(7)
      ]);
      setAuditLogs(logsRes.data.logs || []);
      setAuditSummary(summaryRes.data);
    } catch (error) {
      console.error('Failed to load audit data:', error);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      await userAPI.create(formData);
      toast.success('User created successfully');
      setIsCreateDialogOpen(false);
      setFormData({ email: '', name: '', password: '', role: 'Warehouse Operator' });
      loadUsers();
      if (canViewAudit) loadAuditData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create user');
    }
  };

  const handleRoleChange = async (userId, newRole) => {
    try {
      await userAPI.updateRole(userId, newRole);
      toast.success('Role updated successfully');
      loadUsers();
      if (canViewAudit) loadAuditData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update role');
    }
  };

  const handleToggleStatus = async (user) => {
    if (user.user_id === currentUser.user_id) {
      toast.error('Cannot deactivate your own account');
      return;
    }

    try {
      await userAPI.toggleStatus(user.user_id);
      toast.success(`User ${user.is_active ? 'deactivated' : 'activated'} successfully`);
      loadUsers();
      if (canViewAudit) loadAuditData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update user status');
    }
  };

  const handleDeleteUser = async (user) => {
    if (user.user_id === currentUser.user_id) {
      toast.error('Cannot delete your own account');
      return;
    }

    if (!window.confirm(`Are you sure you want to delete user "${user.name}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await userAPI.delete(user.user_id);
      toast.success('User deleted successfully');
      loadUsers();
      if (canViewAudit) loadAuditData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete user');
    }
  };

  const viewUserHistory = async (user) => {
    setViewingUser(user);
    try {
      const history = await auditAPI.getEntityHistory('user', user.user_id);
      setUserAuditHistory(history.data);
      setIsViewDialogOpen(true);
    } catch (error) {
      toast.error('Failed to load user history');
    }
  };

  const getInitials = (name) => {
    if (!name) return 'U';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  const getRoleBadgeColor = (role) => {
    switch (role) {
      case 'Admin': return 'bg-red-100 text-red-700 border-red-200';
      case 'Store In-Charge': return 'bg-purple-100 text-purple-700 border-purple-200';
      case 'Inventory Controller': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'Warehouse Operator': return 'bg-green-100 text-green-700 border-green-200';
      case 'Auditor': return 'bg-amber-100 text-amber-700 border-amber-200';
      case 'Management Viewer': return 'bg-gray-100 text-gray-700 border-gray-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getActionBadgeColor = (action) => {
    switch (action) {
      case 'create': return 'bg-green-100 text-green-700';
      case 'update': return 'bg-blue-100 text-blue-700';
      case 'delete': return 'bg-red-100 text-red-700';
      case 'role_change': return 'bg-purple-100 text-purple-700';
      case 'status_change': return 'bg-amber-100 text-amber-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const filteredUsers = users.filter(user => 
    user.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.role?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="flex flex-col sm:flex-row justify-between gap-4">
          <TabsList>
            <TabsTrigger value="users" data-testid="users-tab">
              <Users className="w-4 h-4 mr-2" />
              Users
            </TabsTrigger>
            {canViewAudit && (
              <TabsTrigger value="audit" data-testid="audit-tab">
                <History className="w-4 h-4 mr-2" />
                Audit Trail
              </TabsTrigger>
            )}
            <TabsTrigger value="roles" data-testid="roles-tab">
              <Shield className="w-4 h-4 mr-2" />
              Roles & Permissions
            </TabsTrigger>
          </TabsList>

          {isAdmin && activeTab === 'users' && (
            <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button className="bg-[#f59e0b] hover:bg-[#d97706]" data-testid="create-user-btn">
                  <Plus className="w-4 h-4 mr-2" />
                  Create User
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <DialogTitle>Create New User</DialogTitle>
                  <DialogDescription>Add a new user to the system with a specific role.</DialogDescription>
                </DialogHeader>
                <form onSubmit={handleCreateUser} className="space-y-4">
                  <div className="space-y-2">
                    <Label>Full Name *</Label>
                    <Input
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="John Doe"
                      required
                      data-testid="user-name-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Email *</Label>
                    <Input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      placeholder="john@example.com"
                      required
                      data-testid="user-email-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Password *</Label>
                    <Input
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      placeholder="Enter password"
                      required
                      minLength={6}
                      data-testid="user-password-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Role *</Label>
                    <Select value={formData.role} onValueChange={(v) => setFormData({ ...formData, role: v })}>
                      <SelectTrigger data-testid="user-role-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {ROLES.map((role) => (
                          <SelectItem key={role} value={role}>{role}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-gray-500">{ROLE_DESCRIPTIONS[formData.role]}</p>
                  </div>
                  <div className="flex gap-3 pt-4">
                    <Button type="button" variant="outline" onClick={() => setIsCreateDialogOpen(false)} className="flex-1">
                      Cancel
                    </Button>
                    <Button type="submit" className="flex-1 bg-[#f59e0b] hover:bg-[#d97706]" data-testid="user-submit-btn">
                      Create User
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          )}
        </div>

        {/* Users Tab */}
        <TabsContent value="users" className="space-y-4">
          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="border border-gray-200">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">Total Users</p>
                    <p className="text-3xl font-bold tabular-nums">{users.length}</p>
                  </div>
                  <div className="p-3 bg-blue-100 rounded-xl">
                    <Users className="w-6 h-6 text-blue-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="border border-gray-200">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">Active Users</p>
                    <p className="text-3xl font-bold tabular-nums text-green-600">
                      {users.filter(u => u.is_active).length}
                    </p>
                  </div>
                  <div className="p-3 bg-green-100 rounded-xl">
                    <UserCheck className="w-6 h-6 text-green-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="border border-gray-200">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">Inactive</p>
                    <p className="text-3xl font-bold tabular-nums text-red-600">
                      {users.filter(u => !u.is_active).length}
                    </p>
                  </div>
                  <div className="p-3 bg-red-100 rounded-xl">
                    <UserX className="w-6 h-6 text-red-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="border border-gray-200">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">Admins</p>
                    <p className="text-3xl font-bold tabular-nums text-purple-600">
                      {users.filter(u => u.role === 'Admin').length}
                    </p>
                  </div>
                  <div className="p-3 bg-purple-100 rounded-xl">
                    <Shield className="w-6 h-6 text-purple-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Search */}
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Search users..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
              data-testid="user-search-input"
            />
          </div>

          {/* Users Table */}
          <Card className="border border-gray-200">
            <CardContent className="p-0">
              {loading ? (
                <div className="p-8 text-center text-gray-500">Loading users...</div>
              ) : filteredUsers.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <Users className="w-12 h-12 mx-auto mb-2 opacity-20" />
                  <p>No users found</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-gray-50">
                        <TableHead className="font-semibold">User</TableHead>
                        <TableHead className="font-semibold">Email</TableHead>
                        <TableHead className="font-semibold">Role</TableHead>
                        <TableHead className="font-semibold">Auth Type</TableHead>
                        <TableHead className="font-semibold">Status</TableHead>
                        <TableHead className="font-semibold">Joined</TableHead>
                        <TableHead className="font-semibold text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredUsers.map((user) => (
                        <TableRow key={user.user_id} className="hover:bg-gray-50" data-testid={`user-row-${user.email}`}>
                          <TableCell>
                            <div className="flex items-center gap-3">
                              <Avatar className="w-10 h-10">
                                <AvatarImage src={user.picture} />
                                <AvatarFallback className="bg-[#f59e0b] text-white text-sm">
                                  {getInitials(user.name)}
                                </AvatarFallback>
                              </Avatar>
                              <div>
                                <p className="font-medium">{user.name}</p>
                                {user.user_id === currentUser.user_id && (
                                  <span className="text-xs text-[#f59e0b]">(You)</span>
                                )}
                              </div>
                            </div>
                          </TableCell>
                          <TableCell className="text-gray-600">{user.email}</TableCell>
                          <TableCell>
                            {!isAdmin || user.user_id === currentUser.user_id ? (
                              <Badge className={`border ${getRoleBadgeColor(user.role)}`}>
                                {user.role}
                              </Badge>
                            ) : (
                              <Select
                                value={user.role}
                                onValueChange={(v) => handleRoleChange(user.user_id, v)}
                              >
                                <SelectTrigger className="w-44 h-8" data-testid={`role-select-${user.email}`}>
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  {ROLES.map((role) => (
                                    <SelectItem key={role} value={role}>{role}</SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            )}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className="capitalize">
                              {user.auth_type || 'local'}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge className={user.is_active ? 'badge-available' : 'badge-blocked'}>
                              {user.is_active ? 'Active' : 'Inactive'}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-gray-600">
                            {new Date(user.created_at).toLocaleDateString()}
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-1">
                              {canViewAudit && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => viewUserHistory(user)}
                                  title="View History"
                                  data-testid={`history-${user.email}`}
                                >
                                  <History className="w-4 h-4" />
                                </Button>
                              )}
                              {isAdmin && user.user_id !== currentUser.user_id && (
                                <>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleToggleStatus(user)}
                                    className={user.is_active ? 'text-red-600 hover:text-red-700' : 'text-green-600 hover:text-green-700'}
                                    data-testid={`toggle-status-${user.email}`}
                                  >
                                    {user.is_active ? <UserX className="w-4 h-4" /> : <UserCheck className="w-4 h-4" />}
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleDeleteUser(user)}
                                    className="text-red-600 hover:text-red-700"
                                    data-testid={`delete-${user.email}`}
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </Button>
                                </>
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
        </TabsContent>

        {/* Audit Trail Tab */}
        {canViewAudit && (
          <TabsContent value="audit" className="space-y-4">
            {/* Audit Summary */}
            {auditSummary && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="border border-gray-200">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-gray-500">Activity (7 days)</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-3xl font-bold tabular-nums">{auditSummary.action_stats?.length || 0}</p>
                    <p className="text-sm text-gray-500">Total actions recorded</p>
                  </CardContent>
                </Card>
                <Card className="border border-gray-200 md:col-span-2">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-gray-500">Top Active Users</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {auditSummary.top_users?.slice(0, 5).map((u, i) => (
                        <Badge key={i} variant="outline" className="py-1">
                          {u._id?.user_name || 'Unknown'}: {u.count} actions
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Audit Logs Table */}
            <Card className="border border-gray-200">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Recent Audit Logs
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-gray-50">
                        <TableHead className="font-semibold">Timestamp</TableHead>
                        <TableHead className="font-semibold">Action</TableHead>
                        <TableHead className="font-semibold">Entity</TableHead>
                        <TableHead className="font-semibold">Name</TableHead>
                        <TableHead className="font-semibold">Performed By</TableHead>
                        <TableHead className="font-semibold">Details</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {auditLogs.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                            No audit logs found
                          </TableCell>
                        </TableRow>
                      ) : (
                        auditLogs.map((log) => (
                          <TableRow key={log.audit_id} className="hover:bg-gray-50">
                            <TableCell className="text-sm text-gray-600">
                              {new Date(log.timestamp).toLocaleString()}
                            </TableCell>
                            <TableCell>
                              <Badge className={getActionBadgeColor(log.action)}>
                                {log.action.replace('_', ' ')}
                              </Badge>
                            </TableCell>
                            <TableCell className="capitalize">{log.entity_type}</TableCell>
                            <TableCell className="font-medium">{log.entity_name || '-'}</TableCell>
                            <TableCell>
                              <div>
                                <p className="text-sm">{log.performed_by_name}</p>
                                <p className="text-xs text-gray-500">{log.performed_by_role}</p>
                              </div>
                            </TableCell>
                            <TableCell className="max-w-xs truncate text-sm text-gray-600">
                              {log.old_values && log.new_values ? (
                                <span title={JSON.stringify({ old: log.old_values, new: log.new_values })}>
                                  Changed: {Object.keys(log.new_values).join(', ')}
                                </span>
                              ) : log.new_values ? (
                                <span>Created</span>
                              ) : log.old_values ? (
                                <span>Deleted</span>
                              ) : '-'}
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {/* Roles & Permissions Tab */}
        <TabsContent value="roles" className="space-y-4">
          <Card className="border border-gray-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Role-Based Access Control
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {ROLES.map((role) => (
                  <div key={role} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h3 className="font-semibold text-lg">{role}</h3>
                        <p className="text-sm text-gray-500">{ROLE_DESCRIPTIONS[role]}</p>
                      </div>
                      <Badge className={`border ${getRoleBadgeColor(role)}`}>
                        {users.filter(u => u.role === role).length} users
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
                      {['Dashboard', 'Materials', 'GRN', 'Labels', 'Bins', 'Putaway', 'Issues', 'Reports', 'Users', 'Audit'].map((module) => {
                        const moduleKey = module.toLowerCase();
                        const permissions = {
                          'Admin': 'full',
                          'Warehouse Operator': ['dashboard', 'grn', 'labels', 'putaway', 'issues'].includes(moduleKey) ? 'full' : 'read',
                          'Store In-Charge': moduleKey === 'users' ? 'none' : 'full',
                          'Inventory Controller': ['dashboard', 'reports', 'audit'].includes(moduleKey) ? 'full' : 'read',
                          'Auditor': 'read',
                          'Management Viewer': ['dashboard', 'reports'].includes(moduleKey) ? 'read' : 'none'
                        };
                        const access = permissions[role] || 'none';
                        
                        return (
                          <div key={module} className={`text-center p-2 rounded text-xs ${
                            access === 'full' ? 'bg-green-50 text-green-700' :
                            access === 'read' ? 'bg-blue-50 text-blue-700' :
                            'bg-gray-50 text-gray-400'
                          }`}>
                            <div className="font-medium">{module}</div>
                            <div className="capitalize">{access}</div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* User History Dialog */}
      <Dialog open={isViewDialogOpen} onOpenChange={setIsViewDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>User History - {viewingUser?.name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {userAuditHistory.length === 0 ? (
              <p className="text-center text-gray-500 py-4">No history found for this user</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Action</TableHead>
                    <TableHead>Changed By</TableHead>
                    <TableHead>Details</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {userAuditHistory.map((log) => (
                    <TableRow key={log.audit_id}>
                      <TableCell className="text-sm">
                        {new Date(log.timestamp).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <Badge className={getActionBadgeColor(log.action)}>
                          {log.action.replace('_', ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm">{log.performed_by_name}</TableCell>
                      <TableCell className="text-sm">
                        {log.old_values && log.new_values ? (
                          <div className="text-xs">
                            <span className="text-red-600">{JSON.stringify(log.old_values)}</span>
                            <span className="mx-1">→</span>
                            <span className="text-green-600">{JSON.stringify(log.new_values)}</span>
                          </div>
                        ) : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default UserManagement;
