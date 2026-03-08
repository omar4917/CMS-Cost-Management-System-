const router = require('express').Router();
const costController = require('../controllers/costController');
const { auth } = require('../middleware/auth');

router.use(auth);

router.get('/', costController.getContractors);
router.post('/', costController.createContractor);
router.put('/:id', costController.updateContractor);
router.delete('/:id', costController.deleteContractor);
router.get('/:id/payments', costController.getContractorPayments);
router.post('/:id/payments', costController.createContractorPayment);

module.exports = router;
