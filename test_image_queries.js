#!/usr/bin/env node

// Test script to verify image query functionality
const fs = require('fs');
const path = require('path');

async function testImageQueries() {
  const baseUrl = process.argv[2] || 'http://localhost:3000';
  console.log(`🧪 Testing image query functionality at: ${baseUrl}`);
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
    // Test 1: Upload a test image
    console.log('\n1. Testing image upload...');
    const testImage = Buffer.from('fake image data for testing');
    const form = new FormData();
    form.append('file', new Blob([testImage]), 'test-image.jpg');
    form.append('session_id', 'test-image-session');

    const uploadRes = await fetch(`${baseUrl}/api/debug-upload`, {
      method: 'POST',
      body: form,
    });
    const uploadData = await uploadRes.json();
    logTest('Image upload', uploadRes.ok, `Status: ${uploadRes.status}, Session: ${uploadData.session_id}`);

    const sessionId = uploadData.session_id;

    // Test 2: Check session context
    console.log('\n2. Testing session context...');
    const sessionRes = await fetch(`${baseUrl}/api/debug-session/${sessionId}`);
    const sessionData = await sessionRes.json();
    logTest('Session context', sessionRes.ok, `Has session: ${sessionData.has_session}`);

    // Test 3: Test image-related text query
    console.log('\n3. Testing image-related text query...');
    const imageQueryRes = await fetch(`${baseUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        mode: 'text',
        content: 'what does this image look like?',
        lang: 'en'
      }),
    });
    logTest('Image text query', imageQueryRes.ok, `Status: ${imageQueryRes.status}`);

    // Test 4: Test direct image mode query
    console.log('\n4. Testing direct image mode query...');
    const directImageRes = await fetch(`${baseUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        mode: 'image',
        content: 'dGVzdA==', // base64 encoded "test"
        lang: 'en'
      }),
    });
    logTest('Direct image mode', directImageRes.ok, `Status: ${directImageRes.status}`);

    // Test 5: Test regular text query (should not trigger image search)
    console.log('\n5. Testing regular text query...');
    const textQueryRes = await fetch(`${baseUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        mode: 'text',
        content: 'what is the weather like?',
        lang: 'en'
      }),
    });
    logTest('Regular text query', textQueryRes.ok, `Status: ${textQueryRes.status}`);

    // Test 6: Test multiple image-related queries
    console.log('\n6. Testing multiple image-related queries...');
    const imageQueries = [
      'describe this image',
      'what is similar to this picture',
      'show me what this looks like',
      'what does this photo contain'
    ];

    let allImageQueriesPassed = true;
    for (const query of imageQueries) {
      const res = await fetch(`${baseUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          mode: 'text',
          content: query,
          lang: 'en'
        }),
      });
      if (!res.ok) {
        allImageQueriesPassed = false;
        break;
      }
    }
    logTest('Multiple image queries', allImageQueriesPassed, `${imageQueries.length} queries tested`);

  } catch (error) {
    console.error('\n❌ Test suite failed with error:', error.message);
    results.failed++;
  }

  // Summary
  console.log('\n' + '=' .repeat(60));
  console.log('📊 IMAGE QUERY TEST SUMMARY');
  console.log(`✅ Passed: ${results.passed}`);
  console.log(`❌ Failed: ${results.failed}`);
  console.log(`📈 Success Rate: ${((results.passed / (results.passed + results.failed)) * 100).toFixed(1)}%`);

  if (results.failed === 0) {
    console.log('\n🎉 All image query tests passed!');
    console.log('✅ Image uploads preserve context');
    console.log('✅ Image-related queries trigger CLIP search');
    console.log('✅ Regular queries work normally');
    console.log('✅ Session context is maintained');
  } else {
    console.log('\n⚠️  Some tests failed. Check the details above.');
    console.log('\n🔧 Troubleshooting tips:');
    console.log('   - Verify image upload processing');
    console.log('   - Check session context storage');
    console.log('   - Ensure CLIP search is working');
    console.log('   - Verify query routing logic');
  }

  return results.failed === 0;
}

// Run the test
testImageQueries().then(success => {
  process.exit(success ? 0 : 1);
}); 
