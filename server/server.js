const express = require('express');
const fs = require('fs');
const path = require('path');
const cors = require('cors'); // 👈 Add this line
const app = express();
const port = 3000;

// 👇 Enable CORS for all routes (or restrict to your frontend URL)
app.use(cors()); // Allow all origins (for development only)
// OR restrict to your Live Server URL:
// app.use(cors({ origin: 'http://127.0.0.1:5500' }));

// Middleware to parse JSON bodies
app.use(express.json());

// Create i_json directory if it doesn't exist
const jsonDir = path.join(__dirname, '../i_json');
if (!fs.existsSync(jsonDir)) {
    fs.mkdirSync(jsonDir);
}

app.post('/save-json', (req, res) => {
    const jsonData = JSON.stringify(req.body, null, 2);
    const fileName = `skyscanner_answers_${Date.now()}.json`;
    const filePath = path.join(jsonDir, fileName);
    
    fs.writeFile(filePath, jsonData, (err) => {
        if (err) {
            console.error(err);
            return res.status(500).send('Error saving file');
        }
        console.log(`File saved to ${filePath}`);
        res.send({ success: true, path: filePath });
    });
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});