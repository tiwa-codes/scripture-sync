#!/bin/bash
# Test Scripture Sync API endpoints

echo "🧪 Testing Scripture Sync API"
echo "=============================="
echo ""

BASE_URL="http://localhost:8000"

# Test health endpoint
echo "1. Testing health endpoint..."
curl -s "${BASE_URL}/health" | python3 -m json.tool
echo ""

# Test root endpoint
echo "2. Testing root endpoint..."
curl -s "${BASE_URL}/" | python3 -m json.tool
echo ""

# Test verses listing
echo "3. Testing verses listing..."
curl -s "${BASE_URL}/verses/?limit=5" | python3 -m json.tool
echo ""

# Test search
echo "4. Testing search..."
curl -s "${BASE_URL}/search?q=God+so+loved+the+world" | python3 -m json.tool
echo ""

# Test manual transcription
echo "5. Testing manual transcription..."
curl -s -X POST "${BASE_URL}/transcribe?text=For+God+so+loved+the+world" | python3 -m json.tool
echo ""

# Test lock functionality
echo "6. Testing lock endpoint..."
curl -s -X POST "${BASE_URL}/lock" \
  -H "Content-Type: application/json" \
  -d '{"locked": false}' | python3 -m json.tool
echo ""

echo "✅ API tests complete!"
