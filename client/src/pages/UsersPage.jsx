import { useState, useEffect } from 'react';
import { authAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { HiOutlinePlus, HiOutlinePencil, HiOutlineShieldCheck } from 'react-icons/hi';
import { toast } from 'react-toastify';

export default function UsersPage() {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [editUser, setEditUser] = useState(null);
    const [form, setForm] = useState({ username: '', email: '', password: '', firstName: '', lastName: '', role: 'admin', isActive: true });
    const { user: currentUser } = useAuth();

    useEffect(() => { loadUsers(); }, []);

    const loadUsers = async () => {
        try {
            const res = await authAPI.getUsers();
            setUsers(res.data.users || []);
        } catch { toast.error('Failed to load users — superadmin access required'); }
        finally { setLoading(false); }
    };

    const openCreate = () => {
        setEditUser(null);
        setForm({ username: '', email: '', password: '', firstName: '', lastName: '', role: 'admin', isActive: true });
        setShowModal(true);
    };

    const openEdit = (u) => {
        setEditUser(u);
        setForm({ username: u.username, email: u.email || '', password: '', firstName: u.firstName || '', lastName: u.lastName || '', role: u.role, isActive: u.isActive });
        setShowModal(true);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const data = { ...form };
            if (editUser && !data.password) delete data.password;
            if (editUser) {
                await authAPI.updateUser(editUser.id, data);
                toast.success('User updated!');
            } else {
                await authAPI.createUser(data);
                toast.success('User created!');
            }
            setShowModal(false);
            loadUsers();
        } catch (err) { toast.error(err.response?.data?.message || 'Operation failed'); }
    };

    if (loading) return <div className="loading-spinner"><div className="spinner"></div></div>;

    const isSuperAdmin = currentUser?.role === 'superadmin';

    return (
        <div className="page-content">
            <div className="page-header">
                <div>
                    <h1 className="page-title">User Management</h1>
                    <p className="page-subtitle">Manage admin users and access</p>
                </div>
                <div className="page-actions">
                    {isSuperAdmin && (
                        <button className="btn btn-primary" onClick={openCreate}><HiOutlinePlus /> Add User</button>
                    )}
                </div>
            </div>

            {!isSuperAdmin && (
                <div style={{ padding: '16px', background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: '8px', marginBottom: '20px' }}>
                    <p style={{ fontSize: '13px', color: 'var(--accent-amber)' }}>⚠️ Only superadmins can manage users.</p>
                </div>
            )}

            {users.length > 0 ? (
                <div className="table-container">
                    <table className="data-table">
                        <thead><tr><th></th><th>Username</th><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Actions</th></tr></thead>
                        <tbody>
                            {users.map(u => (
                                <tr key={u.id}>
                                    <td>
                                        <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: u.role === 'superadmin' ? 'var(--gradient-purple)' : 'var(--gradient-blue)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 600, fontSize: '14px' }}>
                                            {(u.firstName?.[0] || u.username[0]).toUpperCase()}
                                        </div>
                                    </td>
                                    <td style={{ fontWeight: 500 }}>{u.username}</td>
                                    <td>{u.firstName} {u.lastName}</td>
                                    <td style={{ color: 'var(--text-secondary)' }}>{u.email}</td>
                                    <td>
                                        <span className={`badge ${u.role === 'superadmin' ? 'badge-purple' : 'badge-blue'}`}>
                                            {u.role === 'superadmin' && <HiOutlineShieldCheck style={{ marginRight: '4px' }} />}
                                            {u.role}
                                        </span>
                                    </td>
                                    <td><span className={`badge ${u.isActive ? 'badge-emerald' : 'badge-red'}`}>{u.isActive ? 'Active' : 'Inactive'}</span></td>
                                    <td>
                                        {isSuperAdmin && u.id !== currentUser.id && (
                                            <button className="btn btn-secondary btn-sm" onClick={() => openEdit(u)}><HiOutlinePencil /></button>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            ) : (
                <div className="empty-state"><p>No users found.</p></div>
            )}

            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>{editUser ? 'Edit User' : 'Create Admin User'}</h2>
                            <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
                        </div>
                        <form onSubmit={handleSubmit}>
                            <div className="modal-body">
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Username *</label>
                                        <input className="form-input" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required disabled={!!editUser} />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Email *</label>
                                        <input className="form-input" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
                                    </div>
                                </div>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">First Name</label>
                                        <input className="form-input" value={form.firstName} onChange={(e) => setForm({ ...form, firstName: e.target.value })} />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Last Name</label>
                                        <input className="form-input" value={form.lastName} onChange={(e) => setForm({ ...form, lastName: e.target.value })} />
                                    </div>
                                </div>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">{editUser ? 'New Password (leave blank to keep)' : 'Password *'}</label>
                                        <input className="form-input" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} {...(!editUser ? { required: true } : {})} />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Role</label>
                                        <select className="form-select" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
                                            <option value="admin">Admin</option>
                                            <option value="superadmin">Super Admin</option>
                                        </select>
                                    </div>
                                </div>
                                {editUser && (
                                    <div className="form-group">
                                        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                                            <input type="checkbox" checked={form.isActive} onChange={(e) => setForm({ ...form, isActive: e.target.checked })} />
                                            <span className="form-label" style={{ margin: 0 }}>Active</span>
                                        </label>
                                    </div>
                                )}
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                                <button type="submit" className="btn btn-primary">{editUser ? 'Update' : 'Create'} User</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
