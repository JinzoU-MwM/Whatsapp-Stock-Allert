const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const express = require('express');
const app = express();
const port = 3000;

app.use(express.json());

// Health Check Endpoint
app.get('/health', (req, res) => {
    res.json({
        status: 'online',
        whatsapp_ready: isReady
    });
});

// List Groups Endpoint
app.get('/groups', async (req, res) => {
    if (!isReady) {
        return res.status(503).json({ error: 'WhatsApp client not ready' });
    }
    try {
        const chats = await client.getChats();
        const groups = chats
            .filter(chat => chat.isGroup)
            .map(chat => ({
                name: chat.name,
                id: chat.id._serialized
            }));
        res.json(groups);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Initialize WhatsApp Client
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox']
    }
});

let isReady = false;

client.on('qr', (qr) => {
    console.log('QR RECEIVED. Scan this with WhatsApp:');
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('WhatsApp Client is ready!');
    isReady = true;
});

client.on('authenticated', () => {
    console.log('Authenticated successfully.');
});

client.initialize();

// API Endpoint to send messages
app.post('/send', async (req, res) => {
    if (!isReady) {
        return res.status(503).json({ error: 'WhatsApp client not ready yet' });
    }

    const { number, message, image_path } = req.body;

    if (!number || !message) {
        return res.status(400).json({ error: 'Missing number or message' });
    }

    try {
        // Append @c.us if not present for private chats, or use correct group ID format
        const chatId = number.includes('@') ? number : `${number}@c.us`;

        // Handle Media/Image
        if (image_path) {
            try {
                const media = MessageMedia.fromFilePath(image_path);
                // Send Media with Caption
                await client.sendMessage(chatId, media, { caption: message });
                console.log(`Image sent to ${chatId}`);
            } catch (mediaError) {
                console.error('Error loading media:', mediaError);
                return res.status(400).json({ error: 'Failed to load image file', details: mediaError.message });
            }
        }
        // 2. Send Text Only if no image
        else {
                await client.sendMessage(chatId, message);
                console.log(`Message sent to ${chatId}`);
            }

            res.json({ success: true, status: 'Sent' });
        } catch (error) {
            console.error('Error sending message:', error);
            res.status(500).json({ error: 'Failed to send message', details: error.message });
        }
    });

app.listen(port, () => {
    console.log(`WhatsApp Service listening at http://localhost:${port}`);
});
