const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { User, AuditLog } = require('../models');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../../.env') });

const authController = {
    // POST /api/auth/login
    login: async (req, res, next) => {
        try {
            const { username, password } = req.body;

            if (!username || !password) {
                return res.status(400).json({ message: 'Username and password are required.' });
            }

            const user = await User.findOne({
                where: { username, isActive: true },
            });

            if (!user) {
                return res.status(401).json({ message: 'Invalid credentials.' });
            }

            const isMatch = await bcrypt.compare(password, user.password);
            if (!isMatch) {
                return res.status(401).json({ message: 'Invalid credentials.' });
            }

            // Update last login
            await user.update({ lastLogin: new Date() });

            // Generate token
            const token = jwt.sign(
                { id: user.id, username: user.username, role: user.role, email: user.email, investorId: user.investorId },
                process.env.JWT_SECRET,
                { expiresIn: process.env.JWT_EXPIRES_IN || '7d' }
            );

            // Audit log
            await AuditLog.create({
                userId: user.id,
                action: 'login',
                entityType: 'user',
                entityId: user.id,
                description: `User ${user.username} logged in`,
                ipAddress: req.ip,
            });

            res.json({
                message: 'Login successful',
                token,
                user: {
                    id: user.id,
                    username: user.username,
                    email: user.email,
                    firstName: user.firstName,
                    lastName: user.lastName,
                    role: user.role,
                    avatar: user.avatar,
                    investorId: user.investorId,
                },
            });
        } catch (error) {
            next(error);
        }
    },

    // GET /api/auth/me
    getProfile: async (req, res, next) => {
        try {
            const user = await User.findByPk(req.user.id, {
                attributes: { exclude: ['password'] },
            });

            if (!user) {
                return res.status(404).json({ message: 'User not found.' });
            }

            res.json({ user });
        } catch (error) {
            next(error);
        }
    },

    // PUT /api/auth/profile
    updateProfile: async (req, res, next) => {
        try {
            const { firstName, lastName, email } = req.body;
            const user = await User.findByPk(req.user.id);

            if (!user) {
                return res.status(404).json({ message: 'User not found.' });
            }

            await user.update({ firstName, lastName, email });

            res.json({
                message: 'Profile updated successfully',
                user: {
                    id: user.id,
                    username: user.username,
                    email: user.email,
                    firstName: user.firstName,
                    lastName: user.lastName,
                    role: user.role,
                    avatar: user.avatar,
                    investorId: user.investorId,
                },
            });
        } catch (error) {
            next(error);
        }
    },

    // PUT /api/auth/change-password
    changePassword: async (req, res, next) => {
        try {
            const { currentPassword, newPassword } = req.body;

            if (!currentPassword || !newPassword) {
                return res.status(400).json({ message: 'Current and new password are required.' });
            }

            if (newPassword.length < 6) {
                return res.status(400).json({ message: 'New password must be at least 6 characters.' });
            }

            const user = await User.findByPk(req.user.id);
            const isMatch = await bcrypt.compare(currentPassword, user.password);

            if (!isMatch) {
                return res.status(401).json({ message: 'Current password is incorrect.' });
            }

            const hashedPassword = await bcrypt.hash(newPassword, 10);
            await user.update({ password: hashedPassword });

            res.json({ message: 'Password changed successfully.' });
        } catch (error) {
            next(error);
        }
    },

    // GET /api/auth/users (superadmin only)
    getUsers: async (req, res, next) => {
        try {
            const users = await User.findAll({
                attributes: { exclude: ['password'] },
                order: [['createdAt', 'DESC']],
            });
            res.json({ users });
        } catch (error) {
            next(error);
        }
    },

    // POST /api/auth/users (superadmin only)
    createUser: async (req, res, next) => {
        try {
            const { username, email, password, firstName, lastName, role } = req.body;

            if (!username || !email || !password) {
                return res.status(400).json({ message: 'Username, email, and password are required.' });
            }

            const hashedPassword = await bcrypt.hash(password, 10);

            const user = await User.create({
                username,
                email,
                password: hashedPassword,
                firstName,
                lastName,
                role: role || 'admin',
                investorId: req.body.investorId || null,
            });

            await AuditLog.create({
                userId: req.user.id,
                action: 'create',
                entityType: 'user',
                entityId: user.id,
                description: `Created user ${username}`,
                ipAddress: req.ip,
            });

            res.status(201).json({
                message: 'User created successfully',
                user: {
                    id: user.id,
                    username: user.username,
                    email: user.email,
                    firstName: user.firstName,
                    lastName: user.lastName,
                    role: user.role,
                },
            });
        } catch (error) {
            next(error);
        }
    },

    // PUT /api/auth/users/:id (superadmin only)
    updateUser: async (req, res, next) => {
        try {
            const { id } = req.params;
            const { email, firstName, lastName, role, isActive } = req.body;

            const user = await User.findByPk(id);
            if (!user) {
                return res.status(404).json({ message: 'User not found.' });
            }

            await user.update({ email, firstName, lastName, role, isActive });

            res.json({ message: 'User updated successfully', user: { id: user.id, username: user.username, email: user.email, role: user.role, isActive: user.isActive } });
        } catch (error) {
            next(error);
        }
    },
};

module.exports = authController;
