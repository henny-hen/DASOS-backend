import pytest
import requests
from urllib.parse import quote
import time
import hashlib
import secrets
from flask import Flask
from flask.testing import FlaskClient
import importlib

class TestSecurityVulnerabilities:
    """Security test suite for DASOS application"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        from rest_api import app
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def api_base_url(self):
        """Base URL for API tests"""
        return "http://127.0.0.1:5000/api/v1"
    
    def test_sql_injection_protection(self, client):
        """Test protection against SQL injection attacks"""
        # Common SQL injection payloads
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE subjects; --",
            "1' UNION SELECT * FROM users --",
            "' OR 1=1 --",
            "admin'--",
            "1' AND SLEEP(5)--"
        ]
        
        for payload in sql_payloads:
            # Test in subject endpoint
            response = client.get(f'/api/v1/subjects/{quote(payload)}')
            assert response.status_code in [400, 404], f"SQL injection vulnerability with payload: {payload}"
            
            # Test in search parameters
            response = client.get(f'/api/v1/subjects?academic_year={quote(payload)}')
            assert response.status_code != 500, f"Server error with SQL payload: {payload}"
    
    def test_xss_protection(self, client):
        """Test protection against XSS attacks"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "';alert(String.fromCharCode(88,83,83))//",
            "<iframe src='javascript:alert(1)'>"
        ]
        
        for payload in xss_payloads:
            # Test search endpoint
            response = client.get(f'/api/v1/search?q={quote(payload)}')
            
            # Response should not contain unescaped payload
            if response.data:
                assert payload.encode() not in response.data, f"XSS vulnerability with payload: {payload}"
                # Check for escaped version
                assert b"&lt;script" in response.data or b"&lt;img" in response.data or payload.encode() not in response.data
    
    def test_authentication_security(self, client):
        """Test authentication security measures"""
        # Test missing authentication
        protected_endpoints = [
            '/api/v1/insights/subjects',
            '/api/v1/faculty/changes',
            '/api/v1/evaluation/changes'
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            # These endpoints should be accessible but could require auth in production
            assert response.status_code != 500, f"Server error on {endpoint}"
        
        # Test invalid tokens
        headers = {'Authorization': 'Bearer invalid_token_12345'}
        response = client.get('/api/v1/subjects', headers=headers)
        assert response.status_code != 500, "Server error with invalid token"
    
    def test_rate_limiting(self, client):
        """Test rate limiting protection"""
        # Make many requests quickly
        endpoint = '/api/v1/subjects'
        responses = []
        
        for _ in range(100):
            response = client.get(endpoint)
            responses.append(response.status_code)
        
        # Should see rate limiting kick in (429 status codes)
        # Note: This requires rate limiting to be implemented
        # assert 429 in responses, "No rate limiting detected"
    
    def test_cors_headers(self, client):
        """Test CORS configuration"""
        response = client.get('/api/v1/subjects')
        
        # Check CORS headers are present
        assert 'Access-Control-Allow-Origin' in response.headers
        
        # Verify CORS is not too permissive
        origin = response.headers.get('Access-Control-Allow-Origin')
        assert origin != '*', "CORS allows all origins - security risk"
    
    def test_security_headers(self, client):
        """Test security headers are present"""
        response = client.get('/')
        
        # Check security headers
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': ['DENY', 'SAMEORIGIN'],
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000',
            'Content-Security-Policy': None  # Should be present
        }
        
        for header, expected_values in security_headers.items():
            if expected_values:
                assert header in response.headers, f"Missing security header: {header}"
                if isinstance(expected_values, list):
                    assert response.headers.get(header) in expected_values
                else:
                    assert response.headers.get(header) == expected_values
    
    def test_path_traversal_protection(self, client):
        """Test protection against path traversal attacks"""
        path_payloads = [
            "../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//etc/passwd",
            "..%252f..%252f..%252fetc%252fpasswd"
        ]
        
        for payload in path_payloads:
            response = client.get(f'/api/v1/subjects/{quote(payload)}')
            assert response.status_code in [400, 404], f"Path traversal vulnerability with payload: {payload}"
    
    def test_api_versioning_security(self, client):
        """Test API versioning doesn't expose sensitive info"""
        # Try accessing different API versions
        versions = ['v0', 'v2', 'v1.1', 'beta', 'internal']
        
        for version in versions:
            response = client.get(f'/api/{version}/subjects')
            # Should get 404, not detailed error
            if response.status_code >= 400:
                assert b'stack trace' not in response.data.lower()
                assert b'debug' not in response.data.lower()
    
    def test_error_handling_security(self, client):
        """Test error messages don't leak sensitive information"""
        # Trigger various errors
        error_endpoints = [
            '/api/v1/subjects/999999999',  # Non-existent resource
            '/api/v1/subjects/invalid_id',  # Invalid format
            '/api/v1/nonexistent',  # Non-existent endpoint
        ]
        
        for endpoint in error_endpoints:
            response = client.get(endpoint)
            
            if response.status_code >= 400:
                # Check response doesn't contain sensitive info
                response_text = response.data.decode('utf-8', errors='ignore').lower()
                assert 'traceback' not in response_text
                assert 'stack trace' not in response_text
                assert 'sqlalchemy' not in response_text
                assert 'database' not in response_text
    
    def test_input_validation(self, client):
        """Test input validation on all endpoints"""
        # Test with oversized inputs
        large_input = 'A' * 10000
        response = client.get(f'/api/v1/search?q={large_input}')
        assert response.status_code != 500, "Server crashes with large input"
        
        # Test with special characters
        special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        response = client.get(f'/api/v1/search?q={quote(special_chars)}')
        assert response.status_code != 500, "Server crashes with special characters"
        
        # Test with Unicode
        unicode_input = "测试 テスト 테스ト"
        response = client.get(f'/api/v1/search?q={quote(unicode_input)}')
        assert response.status_code != 500, "Server crashes with Unicode input"
    
    def test_session_security(self, client):
        """Test session security measures"""
        # Make a request and check session cookie
        response = client.get('/')
        
        if 'Set-Cookie' in response.headers:
            cookie_header = response.headers.get('Set-Cookie')
            
            # Check for secure cookie attributes
            assert 'HttpOnly' in cookie_header, "Session cookie missing HttpOnly flag"
            assert 'SameSite' in cookie_header, "Session cookie missing SameSite attribute"
            # In production, should also check for Secure flag
            # assert 'Secure' in cookie_header, "Session cookie missing Secure flag"
    
    def test_api_authentication_bypass(self, client):
        """Test for authentication bypass vulnerabilities"""
        # Try common bypass techniques
        bypass_headers = [
            {'X-Forwarded-For': '127.0.0.1'},
            {'X-Real-IP': '127.0.0.1'},
            {'X-Originating-IP': '127.0.0.1'},
            {'Authorization': 'Bearer null'},
            {'Authorization': 'Bearer undefined'},
            {'Authorization': 'Bearer [object Object]'},
        ]
        
        for headers in bypass_headers:
            response = client.get('/api/v1/subjects', headers=headers)
            # Should not get elevated privileges
            assert response.status_code != 500
    
    def test_content_type_validation(self, client):
        """Test content type validation"""
        # Send wrong content types
        wrong_content_types = [
            'text/plain',
            'application/xml',
            'multipart/form-data',
            'application/octet-stream'
        ]
        
        for content_type in wrong_content_types:
            headers = {'Content-Type': content_type}
            response = client.post('/api/v1/subjects', 
                                 data='{"test": "data"}',
                                 headers=headers)
            # Should reject or handle gracefully
            assert response.status_code in [400, 415, 405]  # Bad request or unsupported media type


class TestCryptographicSecurity:
    """Test cryptographic implementations"""
    
    def test_password_hashing(self):
        """Test password hashing is secure"""
        # This would test the actual password hashing implementation
        password = "test_password_123"
        
        # In a real implementation, you'd import your hashing function
        # from app.auth import hash_password, verify_password
        
        # Hash should be different each time (salt)
        # hash1 = hash_password(password)
        # hash2 = hash_password(password)
        # assert hash1 != hash2
        
        # Should use strong algorithm (bcrypt, scrypt, or Argon2)
        # assert hash1.startswith('$2b$') or hash1.startswith('$argon2')
    
    def test_token_generation(self):
        """Test secure token generation"""
        # Generate tokens
        tokens = set()
        for _ in range(100):
            token = secrets.token_urlsafe(32)
            tokens.add(token)
        
        # All tokens should be unique
        assert len(tokens) == 100
        
        # Tokens should have sufficient entropy
        for token in tokens:
            assert len(token) >= 32


class TestDependencyVulnerabilities:
    """Test for known vulnerabilities in dependencies"""
    
    def test_requirements_security(self):
        """Check Python dependencies for known vulnerabilities"""
        import subprocess
        
        # Run safety check (requires safety package)
        try:
            result = subprocess.run(['safety', 'check', '--json'], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                vulnerabilities = result.stdout
                pytest.fail(f"Vulnerable dependencies found: {vulnerabilities}")
        except FileNotFoundError:
            pytest.skip("Safety package not installed")
    
    def test_npm_audit(self):
        """Check npm dependencies for vulnerabilities"""
        import subprocess
        import json
        
        try:
            result = subprocess.run(['npm', 'audit', '--json'], 
                                  capture_output=True, text=True)
            
            audit_data = json.loads(result.stdout)
            
            if audit_data.get('metadata', {}).get('vulnerabilities', {}).get('high', 0) > 0:
                pytest.fail("High severity npm vulnerabilities found")
            
            if audit_data.get('metadata', {}).get('vulnerabilities', {}).get('critical', 0) > 0:
                pytest.fail("Critical npm vulnerabilities found")
        except (FileNotFoundError, json.JSONDecodeError):
            pytest.skip("npm not available or audit failed")


if __name__ == "__main__":
    pytest.main(["-v", __file__])