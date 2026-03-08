const router = require('express').Router();
const { auth, superAdminOnly } = require('../middleware/auth');
const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');
require('dotenv').config({ path: path.join(__dirname, '../../.env') });

router.use(auth);
router.use(superAdminOnly);

// POST /api/backup/create
router.post('/create', async (req, res, next) => {
    try {
        const backupDir = path.join(__dirname, '../backups');
        if (!fs.existsSync(backupDir)) fs.mkdirSync(backupDir, { recursive: true });

        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `cms_backup_${timestamp}.sql`;
        const filepath = path.join(backupDir, filename);

        const dbUser = process.env.DB_USER || 'root';
        const dbPass = process.env.DB_PASS ? `-p${process.env.DB_PASS}` : '';
        const dbHost = process.env.DB_HOST || 'localhost';
        const dbName = process.env.DB_NAME || 'cms_db';

        const cmd = `mysqldump -h ${dbHost} -u ${dbUser} ${dbPass} ${dbName} > "${filepath}"`;

        exec(cmd, (error) => {
            if (error) {
                return res.status(500).json({ message: 'Backup failed', error: error.message });
            }

            const { AuditLog } = require('../models');
            AuditLog.create({
                userId: req.user.id,
                action: 'backup',
                description: `Database backup created: ${filename}`,
                ipAddress: req.ip,
            });

            res.json({ message: 'Backup created successfully', filename, filepath });
        });
    } catch (error) {
        next(error);
    }
});

// GET /api/backup/list
router.get('/list', async (req, res) => {
    const backupDir = path.join(__dirname, '../backups');
    if (!fs.existsSync(backupDir)) return res.json({ backups: [] });

    const files = fs.readdirSync(backupDir)
        .filter(f => f.endsWith('.sql'))
        .map(f => ({
            name: f,
            size: fs.statSync(path.join(backupDir, f)).size,
            date: fs.statSync(path.join(backupDir, f)).mtime,
        }))
        .sort((a, b) => b.date - a.date);

    res.json({ backups: files });
});

// GET /api/backup/download/:filename
router.get('/download/:filename', (req, res) => {
    const filepath = path.join(__dirname, '../backups', req.params.filename);
    if (!fs.existsSync(filepath)) return res.status(404).json({ message: 'Backup not found.' });
    res.download(filepath);
});

module.exports = router;
