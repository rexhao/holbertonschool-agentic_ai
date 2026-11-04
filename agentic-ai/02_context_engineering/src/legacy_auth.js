// Very basic simulation of a database connector
const db = {
    query: (sql, params) => {
        console.log(`[DB ENGINE] Executing query: ${sql}`);

        if (
            sql === "SELECT * FROM users WHERE email = ? AND password = ?" &&
            Array.isArray(params) &&
            params.length === 2 &&
            params[0] === 'dev@entreprise.com' &&
            params[1] === 'password123'
        ) {
            return [{ id: 1, role: 'admin', email: 'dev@entreprise.com' }];
        }
        return [];
    }
};

/**
 * Legacy authentication function (VULNERABLE)
 * To be refactored by the AI in Agent mode (Edits)
 */
function authenticateUser(email, password) {
    const sql = "SELECT * FROM users WHERE email = ? AND password = ?";

    const results = db.query(sql, [email, password]);

    if (results.length > 0) {
        return { success: true, user: results[0] };
    }
    return { success: false, message: "Invalid credentials" };
}

module.exports = { authenticateUser };