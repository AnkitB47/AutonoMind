#!/usr/bin/env node

// Test script to verify API connectivity and upload functionality
const fs = require('fs');
const path = require('path');

async function testApiConnectivity() {
  const baseUrl = process.argv[2] || 'http://localhost:3000';
  console.log(`Testing API connectivity at: ${baseUrl}`);

  try {
    // Test 1: Debug environment endpoint
    console.log('\n1. Testing /api/debug-env...');
    const envRes = await fetch(`${baseUrl}/api/debug-env`);
    const envData = await envRes.json();
    console.log('✅ Debug env response:', envData);

    // Test 2: Ping endpoint
    console.log('\n2. Testing /api/ping...');
    const pingRes = await fetch(`${baseUrl}/api/ping`);
    const pingData = await pingRes.json();
    console.log('✅ Ping response:', pingData);

    // Test 3: Debug upload endpoint
    console.log('\n3. Testing /api/debug-upload...');
    const testFile = Buffer.from('test content');
    const form = new FormData();
    form.append('file', new Blob([testFile]), 'test.txt');
    form.append('session_id', 'test-session');

    const uploadRes = await fetch(`${baseUrl}/api/debug-upload`, {
      method: 'POST',
      body: form,
    });
    const uploadData = await uploadRes.json();
    console.log('✅ Debug upload response:', uploadData);

    // Test 4: Debug chat endpoint
    console.log('\n4. Testing /api/debug-chat...');
    const chatRes = await fetch(`${baseUrl}/api/debug-chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    const chatData = await chatRes.json();
    console.log('✅ Debug chat response:', chatData);

    console.log('\n🎉 All API tests passed!');
    return true;

  } catch (error) {
    console.error('\n❌ API test failed:', error.message);
    return false;
  }
}

// Run the test
testApiConnectivity().then(success => {
  process.exit(success ? 0 : 1);
}); 
