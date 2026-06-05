import { sequelize } from '../qa-backend-node/db.js';

try {
  console.log('Attempting standard sequelize sync...');
  await sequelize.sync();
  console.log('Sync succeeded!');
} catch (err) {
  console.error('Sync failed with error:');
  console.error(err);
} finally {
  await sequelize.close();
}
