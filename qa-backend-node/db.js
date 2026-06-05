import { Sequelize, DataTypes } from 'sequelize';
import mongoose from 'mongoose';
import { v4 as uuidv4 } from 'uuid';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const dbUrl = process.env.DATABASE_URL;
let sequelize;

if (dbUrl) {
  console.log('Validating DATABASE_URL connection...');
  let connected = false;
  let retries = 3;
  let tempSequelize;

  while (retries > 0 && !connected) {
    try {
      tempSequelize = new Sequelize(dbUrl, {
        dialect: 'postgres',
        logging: false,
        dialectOptions: {
          ssl: process.env.DATABASE_SSL === 'true' ? { rejectUnauthorized: false } : false,
          connectTimeout: 5000
        }
      });
      await tempSequelize.authenticate();
      connected = true;
    } catch (err) {
      retries--;
      console.warn(`PostgreSQL connection attempt failed. Retries remaining: ${retries}. Error: ${err.message}`);
      if (retries > 0) {
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }
  }

  if (connected) {
    console.log('PostgreSQL connection verified successfully. Using Postgres.');
    sequelize = tempSequelize;
  } else {
    console.error('PostgreSQL connection failed after all retries. Falling back to SQLite database.');
    const sqlitePath = path.join(__dirname, 'database.sqlite');
    sequelize = new Sequelize({
      dialect: 'sqlite',
      storage: sqlitePath,
      logging: false,
      pool: {
        max: 1,
        min: 1,
        idle: Infinity,
        acquire: 30000
      }
    });
  }
} else {
  const sqlitePath = path.join(__dirname, 'database.sqlite');
  console.log(`Connecting to SQLite fallback database: ${sqlitePath}`);
  sequelize = new Sequelize({
    dialect: 'sqlite',
    storage: sqlitePath,
    logging: false,
    pool: {
      max: 1,
      min: 1,
      idle: Infinity,
      acquire: 30000
    }
  });
}

// ==========================================
// MONGODB CONNECTION & SCHEMAS
// ==========================================
const mongoUri = process.env.MONGODB_URI;
export let isMongoConnected = false;

export async function connectMongo() {
  if (!mongoUri) {
    console.log('MONGODB_URI is not set. Skipping MongoDB connection.');
    return false;
  }
  try {
    await mongoose.connect(mongoUri);
    console.log('MongoDB connected successfully.');
    isMongoConnected = true;
    return true;
  } catch (err) {
    console.error('Failed to connect to MongoDB:', err.message);
    isMongoConnected = false;
    return false;
  }
}

const projectSchema = new mongoose.Schema({
  _id: { type: String, default: () => uuidv4() },
  name: { type: String, required: true },
  sourceType: { type: String, enum: ['url', 'folder', 'zip'], required: true },
  sourcePath: { type: String, required: true }
}, { timestamps: true });

const testSessionSchema = new mongoose.Schema({
  _id: { type: String, default: () => uuidv4() },
  projectId: { type: String, required: true },
  status: { type: String, enum: ['PENDING', 'RUNNING', 'COMPLETED', 'FAILED'], default: 'PENDING' },
  totalPages: { type: Number, default: 0 },
  totalBugs: { type: Number, default: 0 },
  durationSeconds: { type: Number, default: 0 }
}, { timestamps: true });

const reportSchema = new mongoose.Schema({
  _id: { type: String, default: () => uuidv4() },
  sessionId: { type: String, required: true },
  title: { type: String, required: true },
  description: { type: String, required: true },
  category: { type: String, enum: ['UI', 'API', 'CONSOLE', 'RESOURCE', 'PERFORMANCE'], default: 'UI' },
  severity: { type: String, enum: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'], default: 'MEDIUM' },
  pageUrl: { type: String },
  xpathOrSelector: { type: String },
  screenshotPath: { type: String },
  annotatedScreenshotPath: { type: String },
  videoPath: { type: String },
  rootCause: { type: String },
  suggestedFix: { type: String },
  stepsToReproduce: { type: String },
  browserInfo: { type: String },
  deviceType: { type: String },
  consoleLogs: { type: String },
  networkLogs: { type: String },
  approved: { type: Boolean, default: false }
}, { timestamps: true });

const logSchema = new mongoose.Schema({
  _id: { type: String, default: () => uuidv4() },
  sessionId: { type: String, required: true },
  message: { type: String, required: true },
  level: { type: String, enum: ['INFO', 'SUCCESS', 'WARN', 'ERROR'], default: 'INFO' }
}, { timestamps: true });

export const MongoProject = mongoose.models.Project || mongoose.model('Project', projectSchema);
export const MongoTestSession = mongoose.models.TestSession || mongoose.model('TestSession', testSessionSchema);
export const MongoReport = mongoose.models.Report || mongoose.model('Report', reportSchema);
export const MongoLog = mongoose.models.Log || mongoose.model('Log', logSchema);

// User Model
export const User = sequelize.define('User', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  email: { type: DataTypes.STRING, unique: true, allowNull: false },
  passwordHash: { type: DataTypes.STRING, allowNull: false },
  role: { type: DataTypes.ENUM('Admin', 'Manager', 'Employee', 'Customer'), defaultValue: 'Customer' }
});

// Project Model
export const Project = sequelize.define('Project', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  name: { type: DataTypes.STRING, allowNull: false },
  sourceType: { type: DataTypes.ENUM('url', 'folder', 'zip'), allowNull: false },
  sourcePath: { type: DataTypes.STRING, allowNull: false } // URL or directory path or zip path
});

// TestSession Model
export const TestSession = sequelize.define('TestSession', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  projectId: { type: DataTypes.UUID, allowNull: false },
  status: { type: DataTypes.ENUM('PENDING', 'RUNNING', 'COMPLETED', 'FAILED'), defaultValue: 'PENDING' },
  totalPages: { type: DataTypes.INTEGER, defaultValue: 0 },
  totalBugs: { type: DataTypes.INTEGER, defaultValue: 0 },
  durationSeconds: { type: DataTypes.INTEGER, defaultValue: 0 }
});

// Report (Bug) Model
export const Report = sequelize.define('Report', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  sessionId: { type: DataTypes.UUID, allowNull: false },
  title: { type: DataTypes.STRING, allowNull: false },
  description: { type: DataTypes.TEXT, allowNull: false },
  category: { type: DataTypes.ENUM('UI', 'API', 'CONSOLE', 'RESOURCE', 'PERFORMANCE'), defaultValue: 'UI' },
  severity: { type: DataTypes.ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL'), defaultValue: 'MEDIUM' },
  pageUrl: { type: DataTypes.STRING },
  xpathOrSelector: { type: DataTypes.TEXT },
  screenshotPath: { type: DataTypes.STRING },
  annotatedScreenshotPath: { type: DataTypes.STRING },
  videoPath: { type: DataTypes.STRING },
  rootCause: { type: DataTypes.TEXT },
  suggestedFix: { type: DataTypes.TEXT },
  stepsToReproduce: { type: DataTypes.TEXT },
  browserInfo: { type: DataTypes.STRING },
  deviceType: { type: DataTypes.STRING },
  consoleLogs: { type: DataTypes.TEXT }, // JSON stringified array of logs
  networkLogs: { type: DataTypes.TEXT }, // JSON stringified array of requests
  approved: { type: DataTypes.BOOLEAN, defaultValue: false }
});

// Log Model (For real-time and historical trace logs)
export const Log = sequelize.define('Log', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  sessionId: { type: DataTypes.UUID, allowNull: false },
  message: { type: DataTypes.TEXT, allowNull: false },
  level: { type: DataTypes.ENUM('INFO', 'SUCCESS', 'WARN', 'ERROR'), defaultValue: 'INFO' }
});

// Define Relationships
Project.hasMany(TestSession, { foreignKey: 'projectId', onDelete: 'CASCADE' });
TestSession.belongsTo(Project, { foreignKey: 'projectId' });

TestSession.hasMany(Report, { foreignKey: 'sessionId', onDelete: 'CASCADE' });
Report.belongsTo(TestSession, { foreignKey: 'sessionId' });

TestSession.hasMany(Log, { foreignKey: 'sessionId', onDelete: 'CASCADE' });
Log.belongsTo(TestSession, { foreignKey: 'sessionId' });

export async function initDb() {
  await sequelize.sync();
  console.log('Database synced successfully.');
  await connectMongo();
}

export { sequelize };
