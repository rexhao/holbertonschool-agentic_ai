const userRepository = require('../repositories/user.repository');

class UserExportService {
    async exportUserData(email) {
        const user = userRepository.findByEmail(email);
        if (!user) {
            throw new Error("User not found in the system");
        }
        return { ...user, email };
    }
}

module.exports = new UserExportService();
