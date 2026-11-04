// Very basic simulation of a database connector
const db = {
    query: (sql) => {
        console.log(`[DB ENGINE] Executing query: ${sql}`);
        
        // Simulate vulnerable behavior under a classic SQL injection
        if (sql.includes("' OR '1'='1")) {
            return [{ id: 999, role: 'admin', email: 'hacked@entreprise.com' }]; // Data leak
        }
        
        if (sql === "SELECT * FROM users WHERE email = 'dev@entreprise.com' AND password = 'password123'") {
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
    // CRITICAL VULNERABILITY: SQL injection through string concatenation
    const sql = "SELECT * FROM users WHERE email = '" + email + "' AND password = '" + password + "'";
    
    const results = db.query(sql);

    if (results.length > 0) {
        return { success: true, user: results[0] };
    }
    return { success: false, message: "Invalid credentials" };
}

module.exports = { authenticateUser };