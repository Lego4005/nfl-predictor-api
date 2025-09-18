#!/usr/bin/env node

/**
 * WebSocket Connection Test Script
 * Tests the NFL Predictor WebSocket server functionality
 */

import { WebSocket } from 'ws';

const WS_URL = 'ws://localhost:8080';
const TEST_DURATION = 5000; // 5 seconds

console.log('🔧 NFL Predictor WebSocket Connection Test');
console.log(`📡 Connecting to: ${WS_URL}`);
console.log('');

const ws = new WebSocket(`${WS_URL}?user_id=test_user&token=test_token`);

let connectionAck = false;
let heartbeatReceived = false;
let messagesReceived = 0;

ws.on('open', () => {
  console.log('✅ Connection established');

  // Test subscription
  setTimeout(() => {
    console.log('📝 Subscribing to test channels...');
    ws.send(JSON.stringify({
      event_type: 'user_subscription',
      data: { channel: 'games' },
      timestamp: new Date().toISOString()
    }));

    ws.send(JSON.stringify({
      event_type: 'user_subscription',
      data: { channel: 'predictions' },
      timestamp: new Date().toISOString()
    }));
  }, 1000);

  // Test heartbeat
  setTimeout(() => {
    console.log('💓 Sending heartbeat...');
    ws.send(JSON.stringify({
      event_type: 'heartbeat',
      data: {
        timestamp: new Date().toISOString(),
        client_time: new Date().toISOString()
      },
      timestamp: new Date().toISOString()
    }));
  }, 2000);
});

ws.on('message', (data) => {
  try {
    const message = JSON.parse(data.toString());
    messagesReceived++;

    console.log(`📩 Received: ${message.event_type}`);

    if (message.event_type === 'connection_ack') {
      connectionAck = true;
      console.log(`   ✅ Connection ID: ${message.data.connection_id}`);
      console.log(`   ⏱️  Heartbeat interval: ${message.data.heartbeat_interval}s`);
      console.log(`   🎯 Supported events: ${message.data.supported_events.length}`);
    } else if (message.event_type === 'heartbeat') {
      heartbeatReceived = true;
      console.log(`   💓 Server time: ${message.data.server_time}`);
    } else if (message.event_type === 'notification') {
      console.log(`   📢 ${message.data.message}`);
    } else {
      console.log(`   📄 Data:`, JSON.stringify(message.data, null, 2));
    }
  } catch (error) {
    console.error('❌ Error parsing message:', error);
  }
});

ws.on('close', (code, reason) => {
  console.log(`🔌 Connection closed: ${code} - ${reason}`);
  runTestSummary();
});

ws.on('error', (error) => {
  console.error('❌ WebSocket error:', error.message);
});

// Auto-close after test duration
setTimeout(() => {
  console.log('\n⏰ Test duration completed, closing connection...');
  ws.close(1000, 'Test completed');
}, TEST_DURATION);

function runTestSummary() {
  console.log('\n📊 Test Results:');
  console.log('================');
  console.log(`Connection Acknowledgment: ${connectionAck ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`Heartbeat Response: ${heartbeatReceived ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`Messages Received: ${messagesReceived}`);
  console.log(`Total Test Duration: ${TEST_DURATION}ms`);

  const overallResult = connectionAck && heartbeatReceived && messagesReceived > 0;
  console.log(`\nOverall Result: ${overallResult ? '✅ PASS' : '❌ FAIL'}`);

  if (overallResult) {
    console.log('🎉 WebSocket server is working correctly!');
  } else {
    console.log('❌ WebSocket server has issues that need attention.');
  }

  process.exit(overallResult ? 0 : 1);
}