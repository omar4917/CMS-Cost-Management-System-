const router = require('express').Router();
const costController = require('../controllers/costController');
const { auth } = require('../middleware/auth');

router.use(auth);

router.get('/', costController.getInvestments);
router.post('/', costController.createInvestment);
router.put('/:id', costController.updateInvestment);
router.delete('/:id', costController.deleteInvestment);

module.exports = router;
