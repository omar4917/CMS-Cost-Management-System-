const router = require('express').Router();
const costController = require('../controllers/costController');
const { auth } = require('../middleware/auth');

router.use(auth);
router.get('/', costController.getAuditLogs);

module.exports = router;
