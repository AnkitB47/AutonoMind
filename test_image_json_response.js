// Test script to verify image query JSON responses
const API_BASE = process.env.API_BASE || 'http://localhost:8000';

async function testImageQuery() {
  console.log('Testing image query JSON response...');
  
  try {
    // Test image query
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        mode: 'image',
        content: 'dGVzdA==', // base64 encoded "test"
        session_id: 'test-session-123',
        lang: 'en'
      })
    });

    console.log('Response status:', response.status);
    console.log('Response headers:', Object.fromEntries(response.headers.entries()));
    
    const contentType = response.headers.get('Content-Type');
    if (contentType && contentType.includes('application/json')) {
      const data = await response.json();
      console.log('✅ JSON Response received:');
      console.log('  image_url:', data.image_url);
      console.log('  description:', data.description);
      console.log('  fallback:', data.fallback);
    } else {
      const text = await response.text();
      console.log('❌ Unexpected text response:', text.substring(0, 200));
    }
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
}

async function testTextQueryWithImageContext() {
  console.log('\nTesting text query with image context...');
  
  try {
    // Test text query that should trigger image search
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        mode: 'text',
        content: 'what does this image look similar to?',
        session_id: 'test-session-123',
        lang: 'en'
      })
    });

    console.log('Response status:', response.status);
    console.log('Response headers:', Object.fromEntries(response.headers.entries()));
    
    const contentType = response.headers.get('Content-Type');
    if (contentType && contentType.includes('application/json')) {
      const data = await response.json();
      console.log('✅ JSON Response for text query:');
      console.log('  image_url:', data.image_url);
      console.log('  description:', data.description);
    } else {
      const text = await response.text();
      console.log('Text response (expected for non-image queries):', text.substring(0, 200));
    }
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
}

async function testRegularTextQuery() {
  console.log('\nTesting regular text query...');
  
  try {
    // Test regular text query
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        mode: 'text',
        content: 'Hello, how are you?',
        session_id: 'test-session-123',
        lang: 'en'
      })
    });

    console.log('Response status:', response.status);
    console.log('Response headers:', Object.fromEntries(response.headers.entries()));
    
    const contentType = response.headers.get('Content-Type');
    if (contentType && contentType.includes('application/json')) {
      console.log('❌ Unexpected JSON response for text query');
      const data = await response.json();
      console.log(data);
    } else {
      const text = await response.text();
      console.log('✅ Text response (expected):', text.substring(0, 200));
    }
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  }
}

// Run tests
async function runTests() {
  console.log('🚀 Testing image query JSON responses...\n');
  
  await testImageQuery();
  await testTextQueryWithImageContext();
  await testRegularTextQuery();
  
  console.log('\n✅ Tests completed!');
}

runTests().catch(console.error); 
