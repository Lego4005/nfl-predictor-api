#!/usr/bin/env node

import { spawn } from 'child_process';

console.log('🚀 Testing React Development Server...');
console.log('=' .repeat(50));

// Start the dev server
const devServer = spawn('npm', ['run', 'dev'], {
    stdio: ['pipe', 'pipe', 'pipe'],
    shell: true
});

let serverStarted = false;
let serverOutput = '';

// Listen for output
devServer.stdout.on('data', (data) => {
    const output = data.toString();
    serverOutput += output;
    
    console.log('📝 Server Output:', output.trim());
    
    // Check if server started successfully
    if (output.includes('Local:') || output.includes('localhost')) {
        console.log('✅ React Dev Server: STARTED SUCCESSFULLY');
        serverStarted = true;
        
        // Kill the server after confirming it works
        setTimeout(() => {
            devServer.kill();
            console.log('🛑 Dev server stopped (test complete)');
            process.exit(0);
        }, 2000);
    }
});

devServer.stderr.on('data', (data) => {
    console.error('❌ Server Error:', data.toString());
});

devServer.on('close', (code) => {
    if (!serverStarted) {
        console.log(`❌ Dev server exited with code ${code}`);
        console.log('📋 Full Output:', serverOutput);
    }
});

// Timeout after 10 seconds
setTimeout(() => {
    if (!serverStarted) {
        console.log('⏰ Timeout: Dev server did not start within 10 seconds');
        devServer.kill();
        process.exit(1);
    }
}, 10000);