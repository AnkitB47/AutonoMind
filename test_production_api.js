#!/usr/bin/env node

// Comprehensive production API test script
const fs = require('fs');
const path = require('path');

async function testProductionAPI() {
  const baseUrl = process.argv[2] || 'http://localhost:3000';
  console.log(`🧪 Testing production API at: ${baseUrl}`);
  console.log('=' .repeat(60));

  const results = {
    passed: 0,
    failed: 0,
    tests: []
  };

  function logTest(name, success, details = '') {
    const status = success ? '✅' : '❌';
    const message = success ? 'PASSED' : 'FAILED';
    console.log(`${status} ${name}: ${message}`);
    if (details) console.log(`   ${details}`);
    
    results.tests.push({ name, success, details });
    if (success) results.passed++; else results.failed++;
  }

  try {
    // Test 1: Basic connectivity
    console.log('\n1. Testing basic connectivity...');
    const pingRes = await fetch(`${baseUrl}/api/ping`);
    const pingData = await pingRes.json();
    logTest('Ping endpoint', pingRes.ok, `Status: ${pingRes.status}, Response: ${JSON.stringify(pingData)}`);

    // Test 2: Environment verification
    console.log('\n2. Testing environment configuration...');
    const envRes = await fetch(`${baseUrl}/api/debug-env`);
    const envData = await envRes.json();
    logTest('Environment endpoint', envRes.ok, `Status: ${envRes.status}, Response: ${JSON.stringify(envData)}`);

    // Test 3: Connection details
    console.log('\n3. Testing connection details...');
    const connRes = await fetch(`${baseUrl}/api/debug-connection`);
    const connData = await connRes.json();
    logTest('Connection endpoint', connRes.ok, `Status: ${connRes.status}, Client: ${connData.client_host}`);

    // Test 4: Debug upload with small file
    console.log('\n4. Testing debug upload endpoint...');
    const testFile = Buffer.from('test content for upload verification');
    const form = new FormData();
    form.append('file', new Blob([testFile]), 'test.txt');
    form.append('session_id', 'test-session-' + Date.now());

    const uploadRes = await fetch(`${baseUrl}/api/debug-upload`, {
      method: 'POST',
      body: form,
    });
    const uploadData = await uploadRes.json();
    logTest('Debug upload endpoint', uploadRes.ok, `Status: ${uploadRes.status}, Size: ${uploadData.size} bytes`);

    // Test 5: Debug chat endpoint
    console.log('\n5. Testing debug chat endpoint...');
    const chatRes = await fetch(`${baseUrl}/api/debug-chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    const chatData = await chatRes.json();
    logTest('Debug chat endpoint', chatRes.ok, `Status: ${chatRes.status}, Response: ${JSON.stringify(chatData)}`);

    // Test 6: Large file upload simulation
    console.log('\n6. Testing large file upload simulation...');
    const largeFile = Buffer.alloc(1024 * 1024, 'x'); // 1MB file
    const largeForm = new FormData();
    largeForm.append('file', new Blob([largeFile]), 'large-test.pdf');
    largeForm.append('session_id', 'large-test-' + Date.now());

    const largeUploadRes = await fetch(`${baseUrl}/api/debug-upload`, {
      method: 'POST',
      body: largeForm,
    });
    const largeUploadData = await largeUploadRes.json();
    logTest('Large file upload', largeUploadRes.ok, `Status: ${largeUploadRes.status}, Size: ${largeUploadData.size} bytes`);

    // Test 7: Concurrent requests
    console.log('\n7. Testing concurrent requests...');
    const concurrentPromises = Array(5).fill().map((_, i) => 
      fetch(`${baseUrl}/api/ping`).then(r => r.json())
    );
    const concurrentResults = await Promise.all(concurrentPromises);
    const allSuccessful = concurrentResults.every(r => r.status === 'ok');
    logTest('Concurrent requests', allSuccessful, `5 concurrent requests: ${allSuccessful ? 'all successful' : 'some failed'}`);

    // Test 8: Response time check
    console.log('\n8. Testing response times...');
    const startTime = Date.now();
    await fetch(`${baseUrl}/api/ping`);
    const responseTime = Date.now() - startTime;
    logTest('Response time', responseTime < 5000, `Response time: ${responseTime}ms`);

  } catch (error) {
    console.error('\n❌ Test suite failed with error:', error.message);
    results.failed++;
  }

  // Summary
  console.log('\n' + '=' .repeat(60));
  console.log('📊 TEST SUMMARY');
  console.log(`✅ Passed: ${results.passed}`);
  console.log(`❌ Failed: ${results.failed}`);
  console.log(`📈 Success Rate: ${((results.passed / (results.passed + results.failed)) * 100).toFixed(1)}%`);

  if (results.failed === 0) {
    console.log('\n🎉 All tests passed! Production API is working correctly.');
  } else {
    console.log('\n⚠️  Some tests failed. Check the details above.');
    console.log('\n🔧 Troubleshooting tips:');
    console.log('   - Check if FastAPI is running on port 8000');
    console.log('   - Verify Next.js proxy configuration');
    console.log('   - Check container logs for errors');
    console.log('   - Ensure proper environment variables');
  }

  return results.failed === 0;
}

// Run the test
testProductionAPI().then(success => {
  process.exit(success ? 0 : 1);
}); 
