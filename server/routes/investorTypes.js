const router = require('express').Router();
const costController = require('../controllers/costController');
const { auth } = require('../middleware/auth');

router.use(auth);

router.get('/', costController.getInvestorTypes);
router.post('/', costController.createInvestorType);
router.put('/:id', costController.updateInvestorType);

module.exports = router;
