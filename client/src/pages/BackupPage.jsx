import { useState, useEffect } from 'react';
import { backupAPI } from '../services/api';
import { HiOutlineDatabase, HiOutlineDownload, HiOutlineRefresh } from 'react-icons/hi';
import { toast } from 'react-toastify';

export default function BackupPage() {
    const [backups, setBackups] = useState([]);
    const [loading, setLoading] = useState(true);
    const [creating, setCreating] = useState(false);

    useEffect(() => { loadBackups(); }, []);

    const loadBackups = async () => {
        try { const res = await backupAPI.list(); setBackups(res.data.backups || []); }
        catch { /* ok */ }
        finally { setLoading(false); }
    };

    const createBackup = async () => {
        setCreating(true);
        try {
            const res = await backupAPI.create();
            toast.success(`Backup created: ${res.data.filename}`);
            loadBackups();
        } catch (err) { toast.error(err.response?.data?.message || 'Backup failed — ensure mysqldump is available'); }
        finally { setCreating(false); }
    };

    const downloadBackup = async (filename) => {
        try {
            const res = await backupAPI.download(filename);
            const url = window.URL.createObjectURL(new Blob([res.data]));
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            link.click();
            window.URL.revokeObjectURL(url);
        } catch { toast.error('Download failed'); }
    };

    const formatSize = (bytes) => {
        if (!bytes) return '—';
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / 1048576).toFixed(1) + ' MB';
    };

    if (loading) return <div className="loading-spinner"><div className="spinner"></div></div>;

    return (
        <div className="page-content">
            <div className="page-header">
                <div>
                    <h1 className="page-title">Database Backup</h1>
                    <p className="page-subtitle">Create and manage MySQL database backups</p>
                </div>
                <div className="page-actions">
                    <button className="btn btn-secondary" onClick={loadBackups}><HiOutlineRefresh /> Refresh</button>
                    <button className="btn btn-primary" onClick={createBackup} disabled={creating}>
                        <HiOutlineDatabase /> {creating ? 'Creating...' : 'Create Backup'}
                    </button>
                </div>
            </div>

            {backups.length > 0 ? (
                <div className="table-container">
                    <table className="data-table">
                        <thead><tr><th>Filename</th><th>Size</th><th>Date</th><th>Actions</th></tr></thead>
                        <tbody>
                            {backups.map((b, i) => (
                                <tr key={i}>
                                    <td style={{ fontWeight: 500 }}>📦 {b.name}</td>
                                    <td style={{ color: 'var(--text-muted)' }}>{formatSize(b.size)}</td>
                                    <td style={{ color: 'var(--text-muted)' }}>{new Date(b.date).toLocaleString()}</td>
                                    <td>
                                        <button className="btn btn-secondary btn-sm" onClick={() => downloadBackup(b.name)}><HiOutlineDownload /> Download</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            ) : (
                <div className="empty-state"><div className="empty-state-icon">💾</div><h3>No Backups</h3><p>Create your first database backup to protect your data.</p></div>
            )}
        </div>
    );
}
