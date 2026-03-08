const router = require('express').Router();
const costController = require('../controllers/costController');
const { auth } = require('../middleware/auth');

router.use(auth);

router.get('/', costController.getPaymentSchedules);
router.post('/', costController.createPaymentSchedule);
router.put('/:id', costController.updatePaymentSchedule);

module.exports = router;
