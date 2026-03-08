const router = require('express').Router();
const authController = require('../controllers/authController');
const { auth, superAdminOnly } = require('../middleware/auth');

router.post('/login', authController.login);
router.get('/me', auth, authController.getProfile);
router.put('/profile', auth, authController.updateProfile);
router.put('/change-password', auth, authController.changePassword);
router.get('/users', auth, superAdminOnly, authController.getUsers);
router.post('/users', auth, superAdminOnly, authController.createUser);
router.put('/users/:id', auth, superAdminOnly, authController.updateUser);

module.exports = router;
