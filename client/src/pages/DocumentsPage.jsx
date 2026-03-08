import { useState, useEffect } from 'react';
import { documentAPI } from '../services/api';
import { HiOutlineUpload, HiOutlineSearch, HiOutlineDownload, HiOutlineTrash, HiOutlineDocumentText, HiOutlinePhotograph, HiOutlineFilm } from 'react-icons/hi';
import { toast } from 'react-toastify';

const fileIcons = {
    pdf: '📄', doc: '📝', docx: '📝', xls: '📊', xlsx: '📊', csv: '📊',
    jpg: '🖼️', jpeg: '🖼️', png: '🖼️', gif: '🖼️', svg: '🖼️',
    mp4: '🎬', avi: '🎬', zip: '📦', rar: '📦', txt: '📃',
};

export default function DocumentsPage() {
    const [documents, setDocuments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [uploading, setUploading] = useState(false);

    useEffect(() => { loadData(); }, []);

    const loadData = async () => {
        try {
            const res = await documentAPI.getAll();
            setDocuments(res.data.documents || []);
        } catch { toast.error('Failed to load documents'); }
        finally { setLoading(false); }
    };

    const handleUpload = async (e) => {
        const files = e.target.files;
        if (!files.length) return;
        setUploading(true);
        try {
            for (const file of files) {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('entityType', 'project');
                await documentAPI.upload(formData);
            }
            toast.success(`${files.length} file(s) uploaded!`);
            loadData();
        } catch (err) { toast.error(err.response?.data?.message || 'Upload failed'); }
        finally { setUploading(false); e.target.value = ''; }
    };

    const handleDownload = async (doc) => {
        try {
            const res = await documentAPI.download(doc.id);
            const url = window.URL.createObjectURL(new Blob([res.data]));
            const link = document.createElement('a');
            link.href = url;
            link.download = doc.originalName || doc.filename;
            link.click();
            window.URL.revokeObjectURL(url);
        } catch { toast.error('Download failed'); }
    };

    const handleDelete = async (id) => {
        if (!confirm('Delete this document?')) return;
        try { await documentAPI.delete(id); toast.success('Deleted'); loadData(); }
        catch { toast.error('Delete failed'); }
    };

    const formatSize = (bytes) => {
        if (!bytes) return '—';
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / 1048576).toFixed(1) + ' MB';
    };

    const getIcon = (filename) => {
        const ext = filename?.split('.').pop()?.toLowerCase();
        return fileIcons[ext] || '📎';
    };

    const filtered = documents.filter(d =>
        d.originalName?.toLowerCase().includes(search.toLowerCase()) ||
        d.filename?.toLowerCase().includes(search.toLowerCase())
    );

    if (loading) return <div className="loading-spinner"><div className="spinner"></div></div>;

    return (
        <div className="page-content">
            <div className="page-header">
                <div>
                    <h1 className="page-title">Documents</h1>
                    <p className="page-subtitle">Upload and manage project files</p>
                </div>
                <div className="page-actions">
                    <label className="btn btn-primary" style={{ cursor: 'pointer' }}>
                        <HiOutlineUpload /> {uploading ? 'Uploading...' : 'Upload Files'}
                        <input type="file" multiple hidden onChange={handleUpload} disabled={uploading} />
                    </label>
                </div>
            </div>

            <div className="search-bar">
                <div className="search-input-wrap">
                    <HiOutlineSearch className="search-icon" />
                    <input className="search-input" placeholder="Search documents..." value={search} onChange={(e) => setSearch(e.target.value)} />
                </div>
            </div>

            {filtered.length > 0 ? (
                <div className="table-container">
                    <table className="data-table">
                        <thead><tr><th></th><th>Filename</th><th>Size</th><th>Type</th><th>Uploaded</th><th>Actions</th></tr></thead>
                        <tbody>
                            {filtered.map((doc) => (
                                <tr key={doc.id}>
                                    <td style={{ width: '40px', fontSize: '24px' }}>{getIcon(doc.originalName || doc.filename)}</td>
                                    <td style={{ fontWeight: 500 }}>{doc.originalName || doc.filename}</td>
                                    <td style={{ color: 'var(--text-muted)' }}>{formatSize(doc.fileSize)}</td>
                                    <td><span className="badge badge-gray">{doc.mimeType?.split('/')[1] || '—'}</span></td>
                                    <td style={{ color: 'var(--text-muted)', fontSize: '13px' }}>{new Date(doc.createdAt).toLocaleDateString()}</td>
                                    <td>
                                        <div style={{ display: 'flex', gap: '4px' }}>
                                            <button className="btn btn-secondary btn-sm" onClick={() => handleDownload(doc)}><HiOutlineDownload /></button>
                                            <button className="btn btn-secondary btn-sm" onClick={() => handleDelete(doc.id)} style={{ color: 'var(--accent-red)' }}><HiOutlineTrash /></button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            ) : (
                <div className="empty-state">
                    <div className="empty-state-icon">📁</div>
                    <h3>No Documents</h3>
                    <p>Upload contracts, receipts, and other project files.</p>
                </div>
            )}
        </div>
    );
}
