import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import Redis from 'ioredis';
import pool, { initDB } from './init_db.js';
import { findBestMatch } from './recognitionUtils.js';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json({ limit: '10mb' })); // Allow large payloads (face embeddings/images)

// Setup Redis Client
const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';
const redis = new Redis(redisUrl);

redis.on('connect', () => console.log('Successfully connected to Redis.'));
redis.on('error', (err) => console.error('Redis connection error:', err));

// Helper to determine the current meal slot and generate a greeting
function getMealGreeting(name) {
  const now = new Date();
  
  // VIT Chennai local time zone offset correction if needed.
  // In typical deployment, the server runs in local time.
  const hours = now.getHours();
  const minutes = now.getMinutes();
  const timeVal = hours * 60 + minutes; // Current time in minutes from midnight

  // Breakfast: 6:00 AM - 11:30 AM (360 to 690 mins)
  const breakfastStart = 6 * 60;
  const breakfastEnd = 11 * 60 + 30;

  // Lunch: 12:00 PM - 3:00 PM (720 to 900 mins)
  const lunchStart = 12 * 60;
  const lunchEnd = 15 * 60;

  // Snacks: 4:00 PM - 7:00 PM (960 to 1140 mins)
  const snacksStart = 16 * 60;
  const snacksEnd = 19 * 60;

  // Dinner: 7:30 PM - 10:00 PM (1170 to 1320 mins)
  const dinnerStart = 19 * 60 + 30;
  const dinnerEnd = 22 * 60;

  let mealType = 'Closed';
  let greeting = `Hello, ${name}! The mess is currently closed, but nice seeing you!`;

  if (timeVal >= breakfastStart && timeVal <= breakfastEnd) {
    mealType = 'Breakfast';
    greeting = `Good morning, ${name}! Hope you have a great breakfast!`;
  } else if (timeVal >= lunchStart && timeVal <= lunchEnd) {
    mealType = 'Lunch';
    greeting = `Hope you enjoy your hearty lunch, ${name}!`;
  } else if (timeVal >= snacksStart && timeVal <= snacksEnd) {
    mealType = 'Snacks';
    greeting = `Time for a quick tea break, ${name}!`;
  } else if (timeVal >= dinnerStart && timeVal <= dinnerEnd) {
    mealType = 'Dinner';
    greeting = `Good evening, ${name}! Have a pleasant dinner!`;
  }

  return { mealType, greeting };
}

// 1. RECOGNITION AGENT ENDPOINT
app.post('/api/recognize', async (req, res) => {
  try {
    const { face_embedding } = req.body;

    if (!face_embedding || !Array.isArray(face_embedding) || face_embedding.length !== 128) {
      return res.status(400).json({ error: 'Valid 128-dimensional face embedding is required' });
    }

    // Attempt to retrieve users from Redis cache first
    let users = [];
    const cachedUsers = await redis.get('mess:users_cache');

    if (cachedUsers) {
      users = JSON.parse(cachedUsers);
    } else {
      // Cache miss: query PostgreSQL
      const result = await pool.query('SELECT id, name, reg_no, face_embedding FROM mess_users');
      users = result.rows;
      
      // Store in Redis with a 1-hour expiration
      await redis.set('mess:users_cache', JSON.stringify(users), 'EX', 3600);
    }

    // Perform recognition using utility distance threshold (0.6)
    const matchResult = findBestMatch(face_embedding, users, 0.6);

    if (matchResult.match) {
      const user = matchResult.user;
      const { mealType, greeting } = getMealGreeting(user.name);

      // Cache-based Rate-limiting: prevent marking attendance twice within 30 seconds
      const rateLimitKey = `rate_limit:${user.reg_no}`;
      const isRateLimited = await redis.get(rateLimitKey);

      if (isRateLimited) {
        return res.json({
          match: true,
          name: user.name,
          reg_no: user.reg_no,
          meal_type: mealType,
          greeting: greeting,
          rate_limited: true,
          message: 'Attendance already recorded recently.'
        });
      }

      // Record attendance log in database if meal slot is active and not rate-limited
      if (mealType !== 'Closed') {
        await pool.query(
          'INSERT INTO mess_attendance_logs (user_id, meal_type) VALUES ($1, $2)',
          [user.id, mealType]
        );
      }

      // Set Redis rate-limit key with a 30s TTL
      await redis.set(rateLimitKey, '1', 'EX', 30);

      return res.json({
        match: true,
        name: user.name,
        reg_no: user.reg_no,
        meal_type: mealType,
        greeting: greeting,
        rate_limited: false,
        message: 'Attendance recorded successfully!'
      });
    }

    return res.json({ match: false, message: 'Face not recognized.' });

  } catch (error) {
    console.error('Error in /api/recognize:', error);
    return res.status(500).json({ error: 'Server error processing recognition' });
  }
});

// 2. REGISTRATION AGENT ENDPOINT
app.post('/api/register', async (req, res) => {
  try {
    const { name, reg_no, face_embedding } = req.body;

    if (!name || !reg_no || !face_embedding || !Array.isArray(face_embedding) || face_embedding.length !== 128) {
      return res.status(400).json({ error: 'Name, registration number, and 128-d face embedding are required' });
    }

    // Insert user into PostgreSQL
    try {
      const result = await pool.query(
        'INSERT INTO mess_users (name, reg_no, face_embedding) VALUES ($1, $2, $3) RETURNING id, name, reg_no',
        [name.trim(), reg_no.trim().toUpperCase(), face_embedding]
      );

      // Invalidate Redis cache so that the next request pulls fresh data
      await redis.del('mess:users_cache');

      console.log(`Successfully registered user: ${name} (${reg_no})`);

      return res.status(201).json({
        success: true,
        user: result.rows[0]
      });

    } catch (dbError) {
      // Check for unique key violation on reg_no (pg code 23505)
      if (dbError.code === '23505') {
        return res.status(400).json({ error: `Registration number ${reg_no} is already registered.` });
      }
      throw dbError;
    }

  } catch (error) {
    console.error('Error in /api/register:', error);
    return res.status(500).json({ error: 'Server error registering user' });
  }
});

// 3. RETRIEVE ATTENDANCE LOGS
app.get('/api/logs', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT al.id, u.name, u.reg_no, al.meal_type, al.marked_at 
      FROM mess_attendance_logs al
      JOIN mess_users u ON al.user_id = u.id
      ORDER BY al.marked_at DESC
      LIMIT 15
    `);
    return res.json(result.rows);
  } catch (error) {
    console.error('Error in /api/logs:', error);
    return res.status(500).json({ error: 'Server error retrieving logs' });
  }
});

// Start server and initialize database tables
async function startServer() {
  try {
    await initDB();
    app.listen(PORT, () => {
      console.log(`Backend server is running on http://localhost:${PORT}`);
    });
  } catch (error) {
    console.error('Failed to start server due to DB initialization error:', error);
    process.exit(1);
  }
}

startServer();
