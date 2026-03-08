const router = require('express').Router();
const costController = require('../controllers/costController');
const { auth } = require('../middleware/auth');

router.use(auth);

router.get('/', costController.getCurrencies);
router.put('/:id', costController.updateCurrency);

module.exports = router;
