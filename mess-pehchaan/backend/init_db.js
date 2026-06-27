import pg from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const { Pool } = pg;

// Use connection string from env or default local docker config
const connectionString = process.env.DATABASE_URL || 'postgresql://postgres:postgres@localhost:5432/devassist';

const pool = new Pool({
  connectionString
});

export async function initDB() {
  const client = await pool.connect();
  try {
    console.log('Initializing database tables...');
    
    // Create mess_users table
    await client.query(`
      CREATE TABLE IF NOT EXISTS mess_users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        reg_no VARCHAR(20) UNIQUE NOT NULL,
        face_embedding DOUBLE PRECISION[] NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);
    console.log('Table "mess_users" checked/created.');

    // Create mess_attendance_logs table
    await client.query(`
      CREATE TABLE IF NOT EXISTS mess_attendance_logs (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES mess_users(id) ON DELETE CASCADE,
        meal_type VARCHAR(20) NOT NULL,
        marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);
    console.log('Table "mess_attendance_logs" checked/created.');

  } catch (err) {
    console.error('Error initializing database:', err);
    throw err;
  } finally {
    client.release();
  }
}

export default pool;
