const router = require('express').Router();
const investorController = require('../controllers/investorController');
const { auth } = require('../middleware/auth');

router.use(auth);

router.get('/', investorController.getAll);
router.get('/:id', investorController.getById);
router.post('/', investorController.create);
router.put('/:id', investorController.update);
router.delete('/:id', investorController.delete);

module.exports = router;
