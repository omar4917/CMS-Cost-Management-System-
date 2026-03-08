const router = require('express').Router();
const costController = require('../controllers/costController');
const { auth } = require('../middleware/auth');

router.use(auth);

router.get('/', costController.getCategories);
router.post('/', costController.createCategory);
router.put('/:id', costController.updateCategory);

module.exports = router;
