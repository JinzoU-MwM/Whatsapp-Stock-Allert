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
let latestQr = null;

client.on('qr', (qr) => {
    console.log('QR RECEIVED. Scan this with WhatsApp:');
    qrcode.generate(qr, { small: true });
    latestQr = qr; // Store QR for API retrieval
});

client.on('ready', () => {
    console.log('WhatsApp Client is ready!');
    isReady = true;
    latestQr = null; // Clear QR when connected
});

// Endpoint to get QR Code
app.get('/qr', (req, res) => {
    if (isReady) {
        return res.json({ status: 'connected', qr: null });
    }
    if (latestQr) {
        return res.json({ status: 'scanning', qr: latestQr });
    }
    return res.json({ status: 'initializing', qr: null });
});

app.post('/logout', async (req, res) => {
    console.log('Received Logout Request...');
    try {
        await client.logout();
        // State update handled in 'disconnected' event, but we double ensure here
        console.log('Logout command sent to client.');
        res.json({ success: true, message: 'Logged out successfully' });
    } catch (error) {
        console.error('Error logging out:', error);
        // Even if logout fails (e.g. timeout), we should reset state
        isReady = false;
        latestQr = null;
        try {
             await client.destroy(); 
             await client.initialize();
        } catch (e) { console.error('Force reset failed', e); }
        
        res.status(500).json({ error: 'Failed to logout gracefully, forced reset', details: error.message });
    }
});

client.on('authenticated', () => {
    console.log('Authenticated successfully.');
});

client.on('disconnected', async (reason) => {
    console.log('Client was logged out', reason);
    isReady = false;
    latestQr = null;
    
    // Destroy and Re-initialize to allow new login scan
    try {
        await client.destroy();
    } catch (ignored) {}
    
    console.log('Re-initializing client for new session...');
    client.initialize().catch(err => console.error('Re-init failed:', err));
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
