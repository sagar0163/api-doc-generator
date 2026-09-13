const express = require('express');
const app = express();

app.get('/hello', (req, res) => res.send('hi'));
app.post('/users', createUser);
app.use('/api', apiRouter);
router.get('/account', getAccount);