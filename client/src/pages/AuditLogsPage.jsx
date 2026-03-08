import { useState, useEffect } from 'react';
import { auditLogAPI } from '../services/api';
import { HiOutlineSearch } from 'react-icons/hi';
import { toast } from 'react-toastify';

const actionColors = { create: 'badge-emerald', update: 'badge-blue', delete: 'badge-red', login: 'badge-purple', logout: 'badge-gray', export: 'badge-amber', email_sent: 'badge-cyan', backup: 'badge-amber' };

export default function AuditLogsPage() {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [actionFilter, setActionFilter] = useState('');
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);

    useEffect(() => { loadData(); }, [actionFilter, page]);

    const loadData = async () => {
        try {
            const res = await auditLogAPI.getAll({ action: actionFilter || undefined, page, limit: 50 });
            setLogs(res.data.logs || []);
            setTotal(res.data.total || 0);
        } catch { toast.error('Failed to load audit logs'); }
        finally { setLoading(false); }
    };

    if (loading) return <div className="loading-spinner"><div className="spinner"></div></div>;

    return (
        <div className="page-content">
            <div className="page-header">
                <div>
                    <h1 className="page-title">Audit Trail</h1>
                    <p className="page-subtitle">Track all system activity — {total} total entries</p>
                </div>
            </div>

            <div className="search-bar">
                <select className="filter-select" value={actionFilter} onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}>
                    <option value="">All Actions</option>
                    <option value="create">Create</option>
                    <option value="update">Update</option>
                    <option value="delete">Delete</option>
                    <option value="login">Login</option>
                    <option value="export">Export</option>
                    <option value="email_sent">Email Sent</option>
                    <option value="backup">Backup</option>
                </select>
            </div>

            {logs.length > 0 ? (
                <>
                    <div className="table-container">
                        <table className="data-table">
                            <thead><tr><th>Action</th><th>Description</th><th>Entity</th><th>User</th><th>IP</th><th>Date</th></tr></thead>
                            <tbody>
                                {logs.map(l => (
                                    <tr key={l.id}>
                                        <td><span className={`badge ${actionColors[l.action] || 'badge-gray'}`}>{l.action}</span></td>
                                        <td style={{ maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis' }}>{l.description || '—'}</td>
                                        <td style={{ color: 'var(--text-muted)' }}>{l.entityType ? `${l.entityType} #${l.entityId}` : '—'}</td>
                                        <td style={{ fontWeight: 500 }}>{l.user?.username || 'System'}</td>
                                        <td style={{ color: 'var(--text-muted)', fontSize: '12px' }}>{l.ipAddress || '—'}</td>
                                        <td style={{ color: 'var(--text-muted)', fontSize: '13px', whiteSpace: 'nowrap' }}>{new Date(l.createdAt).toLocaleString()}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    {total > 50 && (
                        <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginTop: '20px' }}>
                            <button className="btn btn-secondary btn-sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Previous</button>
                            <span style={{ padding: '6px 12px', fontSize: '13px', color: 'var(--text-muted)' }}>Page {page} of {Math.ceil(total / 50)}</span>
                            <button className="btn btn-secondary btn-sm" disabled={page >= Math.ceil(total / 50)} onClick={() => setPage(p => p + 1)}>Next</button>
                        </div>
                    )}
                </>
            ) : (
                <div className="empty-state"><div className="empty-state-icon">📋</div><h3>No Audit Logs</h3><p>Activity will be logged as users interact with the system.</p></div>
            )}
        </div>
    );
}
