const router = require('express').Router();
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const { auth } = require('../middleware/auth');
const { Document, AuditLog } = require('../models');

// Configure multer
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        const uploadDir = path.join(__dirname, '../uploads');
        if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir, { recursive: true });
        cb(null, uploadDir);
    },
    filename: (req, file, cb) => {
        const uniqueName = `${Date.now()}-${Math.round(Math.random() * 1E9)}${path.extname(file.originalname)}`;
        cb(null, uniqueName);
    },
});

const upload = multer({
    storage,
    limits: { fileSize: parseInt(process.env.MAX_FILE_SIZE) || 10485760 },
    fileFilter: (req, file, cb) => {
        const allowed = /jpeg|jpg|png|gif|pdf|doc|docx|xls|xlsx|csv|txt|zip/;
        const ext = allowed.test(path.extname(file.originalname).toLowerCase());
        if (ext) cb(null, true);
        else cb(new Error('Invalid file type.'));
    },
});

router.use(auth);

// Upload document
router.post('/', upload.single('file'), async (req, res, next) => {
    try {
        if (!req.file) return res.status(400).json({ message: 'No file uploaded.' });

        const doc = await Document.create({
            name: req.body.name || req.file.originalname,
            originalName: req.file.originalname,
            filePath: req.file.filename,
            fileType: req.file.mimetype,
            fileSize: req.file.size,
            entityType: req.body.entityType,
            entityId: req.body.entityId,
            uploadedBy: req.user.id,
            notes: req.body.notes,
        });

        res.status(201).json({ message: 'Document uploaded', document: doc });
    } catch (error) {
        next(error);
    }
});

// Get documents for entity
router.get('/', async (req, res, next) => {
    try {
        const { entityType, entityId } = req.query;
        const where = {};
        if (entityType) where.entityType = entityType;
        if (entityId) where.entityId = entityId;

        const documents = await Document.findAll({ where, order: [['createdAt', 'DESC']] });
        res.json({ documents });
    } catch (error) {
        next(error);
    }
});

// Download document
router.get('/:id/download', async (req, res, next) => {
    try {
        const doc = await Document.findByPk(req.params.id);
        if (!doc) return res.status(404).json({ message: 'Document not found.' });

        const filePath = path.join(__dirname, '../uploads', doc.filePath);
        if (!fs.existsSync(filePath)) return res.status(404).json({ message: 'File not found on disk.' });

        res.download(filePath, doc.originalName);
    } catch (error) {
        next(error);
    }
});

// Delete document
router.delete('/:id', async (req, res, next) => {
    try {
        const doc = await Document.findByPk(req.params.id);
        if (!doc) return res.status(404).json({ message: 'Document not found.' });

        const filePath = path.join(__dirname, '../uploads', doc.filePath);
        if (fs.existsSync(filePath)) fs.unlinkSync(filePath);

        await doc.destroy();
        res.json({ message: 'Document deleted.' });
    } catch (error) {
        next(error);
    }
});

module.exports = router;
