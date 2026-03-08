const errorHandler = (err, req, res, next) => {
    console.error('Error:', err);

    if (err.name === 'SequelizeValidationError') {
        const errors = err.errors.map(e => ({
            field: e.path,
            message: e.message,
        }));
        return res.status(400).json({ message: 'Validation error', errors });
    }

    if (err.name === 'SequelizeUniqueConstraintError') {
        const field = err.errors[0]?.path || 'field';
        return res.status(409).json({ message: `${field} already exists.` });
    }

    if (err.name === 'SequelizeForeignKeyConstraintError') {
        return res.status(400).json({ message: 'Referenced record does not exist or cannot be deleted due to dependencies.' });
    }

    if (err.name === 'MulterError') {
        if (err.code === 'LIMIT_FILE_SIZE') {
            return res.status(400).json({ message: 'File too large. Maximum size is 10MB.' });
        }
        return res.status(400).json({ message: err.message });
    }

    const statusCode = err.statusCode || 500;
    const message = err.message || 'Internal server error';

    res.status(statusCode).json({
        message,
        ...(process.env.NODE_ENV === 'development' && { stack: err.stack }),
    });
};

module.exports = errorHandler;
